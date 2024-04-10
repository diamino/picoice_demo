# Icestorm VHDL Pico-ICE Demo
Basic VHDL demo projects using the opensource toolchain for the ICE40 FPGAs, involving ghdl-yosys-plugin, yosys, nextpnr and icestorm.
The Makefile can use docker containers to compile the project.
This repository now also contains MicroPython modules (and a Python script) which enable the use of MicroPython on the RP2040 in combination with the ICE FPGA. See below for details.

This example is based on the [icestick_demo](https://github.com/flaminggoat/icestick_demo) by [flaminggoat](https://github.com/flaminggoat).

## Requirements

The following tools need to be installed in order to succesfully run the makefile:
* `yosys` including the GHDL plugin
* `nextpnr-ice40`
* `icepack`
* `bin2uf2` (to build the UF2 file: `make uf2`)
* `dfu-util` (to load directly to CRAM: `make cram`)
* `iceprog` (only for programming: `make prog`)

If the tools don't exist (in the PATH) the makefile tries to run the tools in Docker.

## Usage

After cloning the repo checkout the submodule:
```shell
git submodule update --init --recursive
```

And then in the folder of the examples run:
```shell
make
```

To generate the UF2 file for the Pico-ICE:
```shell
make uf2
```

To load the bitstream directly to configuration memory:
```shell
make cram
```

## Simulation

To run a simulation using the default entity `blinker_tb` and default time (1ms):
```shell
make sim
```
or to simulate a different entity using a different simulation time:
```shell
make sim SIM_ENTITY=counter_tb SIM_TIME=100ns
```

## Docker

To have an easy way of using the different tools in Docker from a shell a script is included to source the aliases:
```shell
source docker-alias.rc
```

## Micropython

The micropython folder contains modules to use the ICE FPGA on the Pico-ICE in combination with MicroPython running on the RP2040. Load all the modules on the RP2040 (exclude `send_bitstream.py`). Make sure to rename `pico-ice.py` to `boot.py`. This will put the Pico-ICE in configuration mode on power-on. By default the RP2040 stays in an infinite configuration loop. To enable normal boot after a certain time-out change the `NORMAL_BOOT_ENABLE` and `BOOT_WAIT` constants in `pico-ice.py`.

The Makefiles in the VHDL examples contain a target `make cram_upy` to load the bitstream into CRAM at the end of the make process using the `send_bitstream.py` script. This script requires the `pyserial` package to be installed (`pip install pyserial`). 

## Components of the `blinky_uart` example
 * UART - Sends data from ROM when data is received.
 * ROM - Stores a small piece of text
 * PLL - The PLL was originally described in verilog and instantiated in VHDL. A VHDL version of the PLL module (created manually) is now used. It is not necessary to use the PLL for this project, it is just instantiated to demonstrate its use. The PLL verilog file was created using this command: `icepll -i 12 -o 60 -p -m -f pll.v`.