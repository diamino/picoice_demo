'''
Pico-ICE utils
'''
import time
import sys
import struct
import select
import micropython
import machine
import rp2
from machine import Pin

CLOCKS_BASE = 0x40008000
CLOCKS_CTRL = 0
CLOCKS_DIV = 4
CLOCKS_CLK_GPOUT0_CTRL_AUXSRC_LSB = 5
CLOCKS_CLK_GPOUT0_CTRL_ENABLE_BITS = 0x00000800
CLOCKS_CLK_GPOUT0_DIV_INT_LSB = 8
GPIO_FUNC_GPCK = 8

CLOCKS_CLK_GPOUT0_CTRL_AUXSRC_VALUE_CLK_USB = 7

ICE_SPI_RX_PIN = 8
ICE_CRAM_CSN_PIN = 9
ICE_SPI_SCK_PIN = 10
ICE_FPGA_RGB0_PIN = 12
ICE_FPGA_RGB1_PIN = 15
ICE_FPGA_RGB2_PIN = 13
ICE_FPGA_CLOCK_PIN = 24
ICE_FPGA_CDONE_PIN = 26
ICE_FPGA_CRESET_B_PIN = 27

BOOT_WAIT = 10
WAIT_AFTER_CRAM_LOAD = 5

cram_sm = None


def clock_gpio_init(gpio_id, src, div):
    pin = Pin(gpio_id)
    gpclk = (0, None, 1, 2, 3)[gpio_id - 21]
    machine.mem32[CLOCKS_BASE + gpclk * 12 + CLOCKS_CTRL] = src << CLOCKS_CLK_GPOUT0_CTRL_AUXSRC_LSB | CLOCKS_CLK_GPOUT0_CTRL_ENABLE_BITS
    machine.mem32[CLOCKS_BASE + gpclk * 12 + CLOCKS_DIV] = div << CLOCKS_CLK_GPOUT0_DIV_INT_LSB
    pin.init(pin.ALT, alt=GPIO_FUNC_GPCK)


def ice_fpga_init(freq_mhz):
    src = CLOCKS_CLK_GPOUT0_CTRL_AUXSRC_VALUE_CLK_USB
    clock_gpio_init(ICE_FPGA_CLOCK_PIN, src, 48 // freq_mhz)


def ice_fpga_start():
    # Stop driving RGB leds from RP2040
    Pin(ICE_FPGA_RGB0_PIN, Pin.IN)
    Pin(ICE_FPGA_RGB1_PIN, Pin.IN)
    Pin(ICE_FPGA_RGB2_PIN, Pin.IN)

    fpga_config_done = Pin(ICE_FPGA_CDONE_PIN, Pin.IN)

    # Get FPGA out of reset
    fpga_reset_pin = Pin(ICE_FPGA_CRESET_B_PIN, Pin.OUT)
    fpga_reset_pin.high()

    timeout = 100
    while not fpga_config_done.value():
        time.sleep_ms(1)
        timeout -= 1
        if timeout == 0:
            ice_fpga_stop()
            return False
    return True


def ice_fpga_stop():
    # Put FPGA in reset
    fpga_reset_pin = Pin(ICE_FPGA_CRESET_B_PIN, Pin.OUT)
    fpga_reset_pin.low()


@rp2.asm_pio(out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=8, out_init=rp2.PIO.OUT_LOW, sideset_init=rp2.PIO.OUT_LOW)
def ice_cram():
    wrap_target()
    nop()           .side(1)
    out(x, 1)
    mov(pins, x)    .side(0) [1]
    wrap()


def ice_cram_state_machine_init():
    global cram_sm
    cram_sm = rp2.StateMachine(1, ice_cram,
                               freq=1_000_000,
                               out_base=Pin(ICE_SPI_RX_PIN),
                               sideset_base=Pin(ICE_SPI_SCK_PIN))
    cram_sm.active(1)


def cram_put_byte(data):
    cram_sm.put(data << 24)


def cram_wait_idle():
    while cram_sm.tx_fifo() != 0:
        pass


def ice_cram_open():
    # Hold FPGA in reset before doing anything with SPI bus
    ice_fpga_stop()

    ice_cram_state_machine_init()

    # SPI_SS low signals FPGA to receive the bitstream
    csn = Pin(ICE_CRAM_CSN_PIN, mode=Pin.OUT)
    csn.value(False)

    # Bring FPGA out of reset after at least 200ns
    time.sleep_us(2)
    Pin(ICE_FPGA_CRESET_B_PIN).value(True)

    # Wait at least 1200us for FPGA to clear internal configuration memory
    time.sleep_us(1300)

    # SPI_SS high for 8 SPI_SCLKs
    csn.value(True)
    cram_put_byte(0)
    cram_wait_idle()
    csn.value(False)


def ice_cram_write(data):
    for b in data:
        cram_put_byte(b)


def ice_cram_close():
    cram_wait_idle()

    # Bring SPI_SS high at end of bitstream and leave it pulled up.
    csn = Pin(ICE_CRAM_CSN_PIN, mode=Pin.OUT)
    csn.value(True)
    time.sleep_us(1)
    csn = Pin(ICE_CRAM_CSN_PIN, Pin.IN, pull=Pin.PULL_UP)

    # Output dummy bytes. CDONE should go high within 100 SCLKs or there was an error with the bitstream.
    for i in range(13):
        cram_put_byte(0)
        if Pin(ICE_FPGA_CDONE_PIN).value():
            break

    # At least another 49 SCLK cycles once CDONE goes high.
    for i in range(7):
        cram_put_byte(0)

    cram_wait_idle()


def receive_bitstream():
    # ignore keyboard interrupts
    micropython.kbd_intr(-1)

    sys.stdout.write('\x06')

    # get file size in 4 byte header
    header = sys.stdin.buffer.read(4)
    file_size = struct.unpack('<L', header)[0]

    ba = bytearray(file_size)

    chunk_size = 128
    n_chunks = file_size // chunk_size
    remaining = file_size - (n_chunks * chunk_size)

    for chunk_no in range(n_chunks):
        sys.stdout.write('\x06')
        chunk = sys.stdin.buffer.read(chunk_size)
        chunk_offset = chunk_no * chunk_size
        ba[chunk_offset: chunk_offset+len(chunk)] = chunk

    sys.stdout.write('\x06')
    chunk_offset = chunk_size * n_chunks
    chunk = sys.stdin.buffer.read(remaining)
    ba[chunk_offset: chunk_offset + remaining] = chunk

    # reenable keyboard interrupts
    micropython.kbd_intr(3)
    time.sleep(WAIT_AFTER_CRAM_LOAD)
    print(f"Received bitstream size: {file_size} bytes...")
    print(f"Last 6 bytes: {bytes(ba[-6:]).hex()}")
    return ba


def main():
    ice_fpga_init(12)
    ice_fpga_start()
    spoll = select.poll()
    spoll.register(sys.stdin, select.POLLIN)
    print("Ready to receive bitstream...")
    c = sys.stdin.read(1) if spoll.poll(BOOT_WAIT * 1000) else None
    spoll.unregister(sys.stdin)
    if c == '\x06':
        bitstream = receive_bitstream()
        ice_cram_open()
        ice_cram_write(bitstream)
        ice_cram_close()
        del bitstream
        print("Bitstream loaded into CRAM...")
    else:
        print("Normal boot...")


if __name__ == '__main__':
    main()
