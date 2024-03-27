PROJ = demo

PIN_DEF = picoice.pcf
DEVICE = up5k
PACKAGE = sg48

TOP_LEVEL = demo
#VHDL_FILES = demo.vhdl rom.vhdl uart/source/uart.vhd
VHDL_FILES = demo.vhdl rom.vhdl pll.vhdl blinker.vhdl uart/source/uart.vhd
TESTBENCH_FILES = blinker-tb.vhdl
SIM_ENTITY ?= blinker_tb
SIM_TIME ?= 1ms
#VERILOG_FILES = pll.v

DOCKER_CMD = docker run --rm -it -v /$(shell pwd)://wrk -w //wrk
ifeq (, $(shell which icepack))
 ICEPACK = $(DOCKER_CMD) ghdl/synth:icestorm icepack
else
 ICEPACK = icepack
endif
ifeq (, $(shell which nextpnr-ice40))
 NEXTPNR = $(DOCKER_CMD) ghdl/synth:nextpnr nextpnr-ice40
else
 NEXTPNR = nextpnr-ice40
endif
ifeq (, $(shell which yosys))
 YOSYS = $(DOCKER_CMD) ghdl/synth:beta yosys
else
 YOSYS = yosys
endif
ifeq (, $(shell which ghdl))
 GHDL = $(DOCKER_CMD) ghdl/synth:beta ghdl
else
 GHDL = ghdl
endif
ifeq (, $(shell which ghdl))
 BIN2UF2 = $(DOCKER_CMD) diamino/uf2utils bin2uf2
else
 BIN2UF2 = bin2uf2
endif
ICEPROG = iceprog
GTKWAVE ?= gtkwave

ifneq ($(VERILOG_FILES),)
MAYBE_READ_VERILOG = read_verilog $(VERILOG_FILES);
endif

all: $(PROJ).bin

%.json: $(VHDL_FILES) %.vhdl
	$(YOSYS) -m ghdl -p \
		"ghdl $^ -e $(TOP_LEVEL); \
		$(MAYBE_READ_VERILOG) \
		synth_ice40 -json $@" > $(PROJ)_yosys.log

%.asc: %.json
	$(NEXTPNR) --$(DEVICE) --package $(PACKAGE) --pcf $(PIN_DEF) --pcf-allow-unconstrained --json $< --asc $@ > $(PROJ)_nextpnr.log

%.bin: %.asc
	$(ICEPACK) $< $@

prog: $(PROJ).bin
	$(ICEPROG) $<

uf2: $(PROJ).bin
	$(BIN2UF2) -o $(PROJ).uf2 $<

clean:
	rm -f $(PROJ).json $(PROJ).asc $(PROJ).bin $(PROJ).uf2 $(PROJ)_*.log

sim:
	$(GHDL) -c $(VHDL_FILES) $(TESTBENCH_FILES) -r $(SIM_ENTITY) --vcd=$(SIM_ENTITY).vcd --wave=$(SIM_ENTITY).ghw --stop-time=$(SIM_TIME)

sim_show:
	$(GTKWAVE) $(SIM_ENTITY).ghw

sim_clean:
	rm -f $(SIM_ENTITY).ghw $(SIM_ENTITY).vcd

.SECONDARY:

.PHONY: all prog clean
