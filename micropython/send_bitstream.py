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


TIMEOUT = 10

if len(sys.argv) <= 1:
    print(f"Usage: {sys.argv[0]} binary_file serial_port")
    sys.exit(1)
# file name
filename = sys.argv[1]
if len(sys.argv) < 3:
    g = slp.grep("Board in FS mode")
    try:
        sp = next(g)
    except StopIteration:
        print("No suitable serial port found!")
        print(f"Try: {sys.argv[0]} binary_file serial_port")
        sys.exit(1)
    port = sp.device
else:
    port = sys.argv[2]

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

    # send file size in 32 bit header
    header = struct.pack('<L', file_size)
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
