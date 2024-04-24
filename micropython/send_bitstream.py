#!/usr/bin/env python
'''
Script to send a bitstream (or any arbitrary binary file) via a serial port

Thanks to Electronut (https://forum.micropython.org/viewtopic.php?t=12431)
'''
import os
import serial
import serial.tools.list_ports as slp
import struct
import sys
import argparse

VERSION = "0.2"

parser = argparse.ArgumentParser(description=f'Pico-ICE MicroPython bitstream loader v{VERSION}')  # noqa: E501

parser.add_argument('filename', type=str,
                    help='The binary (.bin) file to load')
parser.add_argument('-t', '--target', type=str, choices=['cram', 'flash'], default='cram',
                    help='The target to load the bitstream. Options: \'cram\' or \'flash\'. Defaults to \'cram\'.')  # noqa: E501
parser.add_argument('-s', '--serial', type=str,
                    help='Serial port to use. Tries to find a suitable port automatically when ommitted.')  # noqa: E501

args = parser.parse_args()

filename = args.filename

if args.target == 'cram':
    target = 1
elif args.target == 'flash':
    target = 2

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

# open serial
ser = serial.Serial(port, 115200)

file_size = os.path.getsize(filename)
print(f"File size = {file_size} bytes.")

with open(filename, "rb") as fp:

    # send ack to signal bitstream transmission
    ser.write(b'\x06')
    print("Wait for ACK...")
    ser.read_until(expected=b'\x06', size=1)
    print("ACK received...")

    # send target and file size in 48 bit header
    # | target | reserved | size(1) | size(2) | size(3) | size(4) |
    header = struct.pack('<BBL', target, 0, file_size)
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
                print("Done, break.")
                break
            print("Wait for ACK...")
            ser.read_until(expected=b'\x06', size=1)
            print("ACK received...")
            ser.write(bytes)
            ser.flush()
            print(f"Wrote {nbytes} bytes...")
    except Exception as e:
        print(e)

    print("Closing...")

ser.close()
