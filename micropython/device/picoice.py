'''
Pico-ICE utils

by Diamino 2026
'''
import sys
import select
import struct
import time
import micropython
import icecram
import iceflash
import icefpga
# from typing import Iterator

NORMAL_BOOT_ENABLE = False
TRANS_TIMEOUT = 15
BOOT_WAIT = 15
WAIT_AFTER_LOAD = 1
SERIAL_CHUNK_SIZE = 128

MODE_RAM = 1
MODE_FAT = 2
MODE_PAGE = 3

TARGET_CRAM = 1
TARGET_FLASH = 2


def read_serial_header() -> tuple[int, int, int]:
    # ignore keyboard interrupts
    micropython.kbd_intr(-1)

    sys.stdout.write('\x06')

    # get target, mode and file size from 6 byte header
    header = sys.stdin.buffer.read(6)
    target, mode, file_size = struct.unpack('<BBL', header)

    # reenable keyboard interrupts
    micropython.kbd_intr(3)

    return target, mode, file_size


def read_from_serial(file_size: int, chunk_size: int = SERIAL_CHUNK_SIZE):  # -> Iterator[bytes]
    # ignore keyboard interrupts
    micropython.kbd_intr(-1)

    n_chunks = file_size // chunk_size
    remaining = file_size % chunk_size

    for chunk_no in range(n_chunks):
        sys.stdout.write('\x06')
        chunk = sys.stdin.buffer.read(chunk_size)
        yield chunk

    if remaining:
        sys.stdout.write('\x06')
        chunk = sys.stdin.buffer.read(remaining)
        yield chunk
    # reenable keyboard interrupts
    micropython.kbd_intr(3)


def write_to_bytearray(bg, file_size: int) -> bytearray:  # type Iterator[bytes] not supported
    ba = bytearray(file_size)
    offset = 0
    for b in bg:
        ba[offset:offset+len(b)] = b
        offset += len(b)
    return ba


def read_from_bytearray(ba: bytearray, chunk_size: int):  # type Iterator[bytes] not supported
    n_chunks = len(ba) // chunk_size
    remaining = len(ba) % chunk_size
    for chunk_no in range(n_chunks):
        offset = chunk_no * chunk_size
        yield ba[offset:offset + chunk_size]
    if remaining:
        yield ba[-remaining:]


def write_to_cram(bg) -> None:  # type Iterator[bytes] not supported
    icecram.ice_cram_open()
    for b in bg:
        icecram.ice_cram_write(b)
    icecram.ice_cram_close()


def write_to_flash(bg) -> None:  # type Iterator[bytes] not supported
    buffer = bytearray(iceflash.ICE_FLASH_PAGE_SIZE)
    bufptr = 0
    flash_offset = 0
    iceflash.ice_flash_open()
    for b in bg:
        # Calculate space left in buffer
        bufspace = len(buffer) - bufptr

        buffer[bufptr:min(bufptr+len(b), len(buffer))] = b[:bufspace]
        bufptr += len(b)
        if bufptr >= len(buffer):
            # Send buffer to flash
            iceflash.ice_flash_write(flash_offset, buffer)
            flash_offset += len(buffer)
        if len(b) > bufspace:
            buffer[0:len(b) - bufspace] = b[bufspace:]
            bufptr = len(b) - bufspace
        elif len(b) == bufspace:
            bufptr = 0
    if bufptr < len(buffer) and bufptr != 0:  # Some data left in buffer
        iceflash.ice_flash_write(flash_offset, buffer[:bufptr])
    icefpga.ice_fpga_start()
    del buffer


def load_from_serial(wait_after_load: int) -> None:
    target, mode, file_size = read_serial_header()
    if mode == MODE_RAM:
        bitstream = write_to_bytearray(read_from_serial(file_size), file_size)
        time.sleep(wait_after_load)
        print(f"Received bitstream size: {len(bitstream)} bytes...")
        print(f"Last 6 bytes: {bytes(bitstream[-6:]).hex()}")

        if target == TARGET_CRAM:
            write_to_cram(read_from_bytearray(bitstream, 128))
        elif target == TARGET_FLASH:
            write_to_flash(read_from_bytearray(bitstream, iceflash.ICE_FLASH_PAGE_SIZE))
        del bitstream  # Free up memory
    elif mode == MODE_FAT:
        # TODO
        pass
    elif mode == MODE_PAGE:
        if target == TARGET_CRAM:
            write_to_cram(read_from_serial(file_size))
        elif target == TARGET_FLASH:
            # write_to_flash(read_from_serial(file_size))
            # Seems not to work. Maybe receieving via serial is too slow
            pass
        time.sleep(wait_after_load)


def wait_for_transmission(timeout: int = TRANS_TIMEOUT):
    spoll = select.poll()
    spoll.register(sys.stdin, select.POLLIN)
    c = sys.stdin.read(1) if spoll.poll(timeout * 1000) else None
    if c == '\x06':
        load_from_serial(WAIT_AFTER_LOAD)
        print("Bitstream loaded...")
    spoll.unregister(sys.stdin)


def main():
    icefpga.ice_fpga_init(12)
    icefpga.ice_fpga_start()
    print("Ready to receive bitstream...")
    while True:
        wait_for_transmission(BOOT_WAIT)
        if NORMAL_BOOT_ENABLE:
            break

    print("Normal boot...")


if __name__ == '__main__':
    main()
