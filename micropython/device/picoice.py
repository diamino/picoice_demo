'''
Pico-ICE utils
'''
import time
import sys
import struct
import select
import micropython
import icefpga
import icecram
import iceflash

NORMAL_BOOT_ENABLE = False
TRANS_TIMEOUT = 15
BOOT_WAIT = 15
WAIT_AFTER_CRAM_LOAD = 1
CHUNK_SIZE_DEFAULT = 128


def receive_bitstream(chunk_size=CHUNK_SIZE_DEFAULT):
    # ignore keyboard interrupts
    micropython.kbd_intr(-1)

    sys.stdout.write('\x06')

    # get target and file size in 6 byte header
    header = sys.stdin.buffer.read(6)
    target, _, file_size = struct.unpack('<BBL', header)

    ba = bytearray(file_size)

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
    return target, ba


def load_from_serial(wait_after_load):
    target, bitstream = receive_bitstream()

    time.sleep(wait_after_load)
    print(f"Received bitstream size: {len(bitstream)} bytes...")
    print(f"Last 6 bytes: {bytes(bitstream[-6:]).hex()}")

    if target == 1:
        icecram.ice_cram_open()
        icecram.ice_cram_write(bitstream)
        icecram.ice_cram_close()
    elif target == 2:
        iceflash.ice_flash_open()
        iceflash.ice_flash_write(0, bitstream)
        icefpga.ice_fpga_start()

    del bitstream
    return True


def wait_for_transmission(timeout=TRANS_TIMEOUT):
    spoll = select.poll()
    spoll.register(sys.stdin, select.POLLIN)
    c = sys.stdin.read(1) if spoll.poll(timeout * 1000) else None
    if c == '\x06':
        load_from_serial(WAIT_AFTER_CRAM_LOAD)
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
