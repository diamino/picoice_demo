# Icestorm VDHL Pico-ICE Demo
Basic VHDL demo project using the opensource toolchain for the ICE40 FPGAs, involving ghdl-yosys-plugin, yosys, nextpnr and icestorm.
The Makefile can use docker containers to compile the project.

## Requirements

The following tools need to be installed in order to succesfully run the makefile:
* `yosys` including the GHDL plugin
* `nextpnr-ice40`
* `icepack`
* `iceprog` (only for programming: `make prog`)

If the tools don't exist (in the PATH) the makefile tries to run the tools in Docker.

## Usage

After cloning the repo checkout the submodule:
```shell
git submodule update --init --recursive
```

And then run:
```shell
make
```

To run a simulation using the default entity `blinker_tb` and default time (1ms):
```shell
make sim
```
or to simulate a different entity using a different simulation time:
```shell
make sim SIM_ENTITY=counter_tb SIM_TIME=100ns
```

To have an easy way of using the different tools in Docker from a shell a script is included to source the aliases:
```shell
source docker-alias.rc
```

## Components
 * UART - Sends data from ROM when data is received.
 * ROM - Stores a small piece of text
 * PLL - The PLL was originally described in verilog and instantiated in VHDL. A VHDL version of the PLL module (created manually) is now used. It is not necessary to use the PLL for this project, it is just instantiated to demonstrate its use. The PLL verilog file was created using this command: `icepll -i 12 -o 60 -p -m -f pll.v`.