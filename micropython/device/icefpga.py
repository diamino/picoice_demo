'''
Module for Pico-ICE to control the FPGA
'''
import time
import machine
from machine import Pin
from icepins import (ICE_FPGA_CLOCK_PIN,
                     ICE_FPGA_RGB0_PIN,
                     ICE_FPGA_RGB1_PIN,
                     ICE_FPGA_RGB2_PIN,
                     ICE_FPGA_CDONE_PIN,
                     ICE_FPGA_CRESET_B_PIN)


CLOCKS_BASE = 0x40008000
CLOCKS_CTRL = 0
CLOCKS_DIV = 4
CLOCKS_CLK_GPOUT0_CTRL_AUXSRC_LSB = 5
CLOCKS_CLK_GPOUT0_CTRL_ENABLE_BITS = 0x00000800
CLOCKS_CLK_GPOUT0_DIV_INT_LSB = 8
GPIO_FUNC_GPCK = 8

CLOCKS_CLK_GPOUT0_CTRL_AUXSRC_VALUE_CLK_USB = 7


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
