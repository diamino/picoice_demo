'''
Module for Pico-ICE FPGA configuration memory handling
'''
import time
from machine import Pin
import rp2
import icefpga
from icepins import (ICE_SPI_RX_PIN,
                     ICE_SPI_SCK_PIN,
                     ICE_CRAM_CSN_PIN,
                     ICE_FPGA_CDONE_PIN,
                     ICE_FPGA_CRESET_B_PIN)

SPI_SM_FREQ = 12_000_000

cram_sm = None


@rp2.asm_pio(out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=8, out_init=rp2.PIO.OUT_LOW, sideset_init=rp2.PIO.OUT_LOW)
def ice_cram():
    wrap_target()
    nop()           .side(1)
    out(x, 1)
    mov(pins, x)    .side(0) [1]
    wrap()


def ice_cram_state_machine_init():
    global cram_sm
    cram_sm = rp2.StateMachine(0, ice_cram,
                               freq=SPI_SM_FREQ,
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
    icefpga.ice_fpga_stop()

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

    # Output dummy bytes. CDONE should go high within 100 SCLKs or there 
    #  was an error with the bitstream.
    for i in range(13):
        cram_put_byte(0)
        if Pin(ICE_FPGA_CDONE_PIN).value():
            break

    # At least another 49 SCLK cycles once CDONE goes high.
    for i in range(7):
        cram_put_byte(0)

    cram_wait_idle()
