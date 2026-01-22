#!/usr/bin/env python
'''
Script to send a bitstream (or any arbitrary binary file) via a serial port

Thanks to Electronut (https://forum.micropython.org/viewtopic.php?t=12431)

by Diamino 2026
'''
import os
import serial
import serial.tools.list_ports as slp
import struct
import sys
import argparse

VERSION = "0.2"
TARGETS = {'cram': 1, 'flash': 2}
MODES = {'ram': 1, 'fat': 2, 'direct': 3}

parser = argparse.ArgumentParser(description=f'Pico-ICE MicroPython bitstream loader v{VERSION}')  # noqa: E501

parser.add_argument('filename', type=str,
                    help='The binary (.bin) file to load')
parser.add_argument('-t', '--target', type=str, choices=['cram', 'flash'], default='cram',
                    help='The target to load the bitstream. Options: \'cram\' or \'flash\'. Defaults to \'cram\'.')  # noqa: E501
parser.add_argument('-m', '--mode', type=str, choices=['ram', 'fat', 'direct'], default='ram',
                    help='The mode used by the RP2040 to cache the bitstream. Options: \'ram\', \'fat\' or \'direct\'. Defaults to \'ram\'.')  # noqa: E501
parser.add_argument('-s', '--serial', type=str,
                    help='Serial port to use. Tries to find a suitable port automatically when ommitted.')  # noqa: E501

args = parser.parse_args()

filename = args.filename

target = TARGETS[args.target]
mode = MODES[args.mode]

if args.serial:
    port = args.serial
else:
    g = slp.grep("Board in FS mode")
    try:
        sp = next(g)
    except StopIteration:
        print("No suitable serial port found!")
        print(f"Try: {sys.argv[0]} binary_file -s serial_port")
        sys.exit(1)
    port = sp.device

print(f'>>> Pico-ICE MicroPython bitstream loader v{VERSION} <<<\n')

# open serial
ser = serial.Serial(port, 115200)

file_size = os.path.getsize(filename)
print(f"File size = {file_size} bytes")
print(f"Target: {args.target}")

with open(filename, "rb") as fp:

    # send ack to signal bitstream transmission
    ser.write(b'\x06')
    print("\nWait for ACK...")
    ser.read_until(expected=b'\x06', size=1)
    print("ACK received...")

    # send target and file size in 48 bit header
    # | target | mode | size(1) | size(2) | size(3) | size(4) |
    #
    # target: 1 = CRAM, 2 = FPGA Flash
    # mode: 1 = cache in RAM, 2 = cache in FAT, 3 = cache per chunk/page
    header = struct.pack('<BBL', target, mode, file_size)
    ser.write(header)
    ser.flush()

    # send file in chunks
    chunk_size = 128
    try:
        nbytes = 0
        while True:
            bytes = fp.read(chunk_size)
            nbytes += len(bytes)
            if not bytes:
                print("\nDone...")
                break
            ser.read_until(expected=b'\x06', size=1)
            print(".", end='', flush=True)
            ser.write(bytes)
            ser.flush()
        print(f"Wrote {nbytes} bytes...")
    except Exception as e:
        print(e)

    # print("Closing...")

ser.close()
