'''
Pico-ICE utils
'''
import time
import machine
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


def ice_cram_open():
    # Hold FPGA in reset before doing anything with SPI bus
    ice_fpga_stop()

    # cram_state_machine_init()

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
    # cram_put_byte(0)
    # cram_wait_idle()
    csn.value(False)


def main():
    ice_fpga_init(12)
    ice_fpga_start()


if __name__ == '__main__':
    main()
