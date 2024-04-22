from machine import SPI, Pin
import icefpga
import time
import struct

ICE_FLASH_CSN_PIN = 9
ICE_SPI_SCK_PIN = 10
ICE_SPI_RX_PIN = 8
ICE_SPI_TX_PIN = 11
ICE_SPI_BAUDRATE = 1_000_000

ICE_FLASH_BLOCK_SIZE = 65536
ICE_FLASH_SECTOR_SIZE = 4096
ICE_FLASH_PAGE_SIZE = 256

FLASH_CMD_PROGRAM_PAGE = const(0x02)
FLASH_CMD_READ = const(0x03)
FLASH_CMD_ENABLE_WRITE = const(0x06)
FLASH_CMD_STATUS = const(0x05)
FLASH_CMD_SECTOR_ERASE = const(0x20)
FLASH_CMD_READ_ID = const(0x9f)
FLASH_CMD_BLOCK_ERASE = const(0xD8)
FLASH_CMD_CHIP_ERASE = const(0xC7)
FLASH_CMD_RELEASE_POWERDOWN = const(0xAB)
FLASH_CMD_POWERDOWN = const(0xB9)
FLASH_CMD_NOP = const(0xFF)

# status register bits
FLASH_STATUS_BUSY_MASK = const(0x01)

FLASH_MFG = 0xef   # Winbond
FLASH_ID = 0x4016  # W25Q32 memory type and capacity

pincs = None
spi = None


def wait():
    pincs(0)
    spi.write(bytes([FLASH_CMD_STATUS]))
    while FLASH_STATUS_BUSY_MASK & spi.read(1, FLASH_CMD_NOP)[0]:
        time.sleep_us(10)
    pincs(1)


def wakeup():
    pincs(0)
    spi.write(bytes([FLASH_CMD_RELEASE_POWERDOWN]))
    pincs(1)


def info():
    pincs(0)
    time.sleep_us(1000)  # Flash wake-up delay
    spi.write(bytes([FLASH_CMD_READ_ID]))
    result = spi.read(3, FLASH_CMD_NOP)
    pincs(1)
    return result[0], result[1] << 8 | result[2]


def check_chip():
    chip_info = info()
    return (chip_info[0] == FLASH_MFG) and (chip_info[1] == FLASH_ID)


def enable_write():
    pincs(0)
    spi.write(bytes([FLASH_CMD_ENABLE_WRITE]))
    pincs(1)


def erase_chip():
    enable_write()
    pincs(0)
    spi.write(bytes([FLASH_CMD_CHIP_ERASE]))
    pincs(1)
    wait()


def erase_block(address: int):
    if (address % ICE_FLASH_BLOCK_SIZE) != 0:
        return False
    addr_bytes = struct.pack(">L", address)[1:]
    enable_write()
    pincs(0)
    spi.write(bytes([FLASH_CMD_BLOCK_ERASE]) + addr_bytes)
    pincs(1)
    wait()


def erase_sector(address: int):
    if (address % ICE_FLASH_SECTOR_SIZE) != 0:
        return False
    addr_bytes = struct.pack(">L", address)[1:]
    enable_write()
    pincs(0)
    spi.write(bytes([FLASH_CMD_SECTOR_ERASE]) + addr_bytes)
    pincs(1)
    wait()


def program_page(address: int, page: bytes):
    if (address % ICE_FLASH_PAGE_SIZE) != 0:
        return False
    addr_bytes = struct.pack(">L", address)[1:]
    enable_write()
    pincs(0)
    spi.write(bytes([FLASH_CMD_PROGRAM_PAGE]) + addr_bytes)
    spi.write(page)
    pincs(1)
    wait()


def ice_flash_open():
    global spi, pincs
    icefpga.ice_fpga_stop()

    pincs = Pin(ICE_FLASH_CSN_PIN, mode=Pin.OUT)
    pincs(1)
    spi = SPI(1, ICE_SPI_BAUDRATE, polarity=1, phase=1, sck=Pin(ICE_SPI_SCK_PIN), mosi=Pin(ICE_SPI_TX_PIN), miso=Pin(ICE_SPI_RX_PIN))

    wakeup()
    time.sleep_us(1000)  # Flash wake-up delay
    wait()

    if check_chip():
        print("Detected supported flash chip...")
    else:
        print("Flash chip not supported!")


def ice_flash_write(address: int, data: bytes):
    for offset in range(0, len(data), ICE_FLASH_PAGE_SIZE):
        if ((address + offset) % ICE_FLASH_SECTOR_SIZE) == 0:
            erase_sector(address + offset)
        program_page(address + offset, data[offset:offset + ICE_FLASH_PAGE_SIZE])
