# Icestorm VDHL Pico-ICE Demo
Basic VHDL demo project using the opensource toolchain for the ICE40 FPGAs, involving ghdl-yosys-plugin, yosys, nextpnr and icestorm.
The Makefile can use docker containers to compile the project.

## Requirements

The following tools need to be installed in order to succesfully run the makefile:
* `yosys` including the GHDL plugin
* `nextpnr-ice40`
* `icepack`
* `iceprog`

If the tools don't exist (in the PATH) the makefile tries to run the tools in Docker.

## Usage

After cloning the repo checkout the submodule:
```
git submodule update --init --recursive
```

And then run:
```
make
```

## Components
 * UART - Sends data from ROM when data is received.
 * ROM - Stores a small piece of text
 * PLL - The PLL is described in verilog and instantiated in VHDL. It is not necessary to use the PLL for this project, it is just instantiated to demonstrate its use. The PLL verilog file was created using this command: `icepll -i 12 -o 60 -p -m -f pll.v`.