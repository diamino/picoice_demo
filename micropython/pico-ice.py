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

NORMAL_BOOT_ENABLE = False
BOOT_WAIT = 15
WAIT_AFTER_CRAM_LOAD = 5
CHUNK_SIZE_DEFAULT = 128


def receive_bitstream(chunk_size=CHUNK_SIZE_DEFAULT):
    # ignore keyboard interrupts
    micropython.kbd_intr(-1)

    sys.stdout.write('\x06')

    # get file size in 4 byte header
    header = sys.stdin.buffer.read(4)
    file_size = struct.unpack('<L', header)[0]

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
    return ba


def cram_load_from_serial(wait_after_load):
    bitstream = receive_bitstream()

    time.sleep(wait_after_load)
    print(f"Received bitstream size: {len(bitstream)} bytes...")
    print(f"Last 6 bytes: {bytes(bitstream[-6:]).hex()}")

    icecram.ice_cram_open()
    icecram.ice_cram_write(bitstream)
    icecram.ice_cram_close()
    del bitstream
    return True


def main():
    icefpga.ice_fpga_init(12)
    icefpga.ice_fpga_start()
    spoll = select.poll()
    spoll.register(sys.stdin, select.POLLIN)
    print("Ready to receive bitstream...")
    while True:
        c = sys.stdin.read(1) if spoll.poll(BOOT_WAIT * 1000) else None
        if c == '\x06':
            cram_load_from_serial(WAIT_AFTER_CRAM_LOAD)
            print("Bitstream loaded into CRAM...")
        if NORMAL_BOOT_ENABLE:
            break
    spoll.unregister(sys.stdin)

    print("Normal boot...")


if __name__ == '__main__':
    main()
