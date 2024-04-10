PROJ = nightrider

PIN_DEF = picoice.pcf
DEVICE = up5k
PACKAGE = sg48

TOP_LEVEL = top
VHDL_FILES = top.vhdl prescaler.vhd
TESTBENCH_FILES = prescaler_tb.vhd
SIM_ENTITY ?= prescaler_tb
SIM_TIME ?= 1ms

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
DFUUTIL = dfu-util
UPY_SEND = ../micropython/send_bitstream.py
GTKWAVE ?= gtkwave

ifneq ($(VERILOG_FILES),)
MAYBE_READ_VERILOG = read_verilog $(VERILOG_FILES);
endif

all: $(PROJ).bin

sim: $(SIM_ENTITY).ghw

%.json: $(VHDL_FILES)
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

cram: $(PROJ).bin
	$(DFUUTIL) -a 1 -D $<

cram_upy: $(PROJ).bin
	$(UPY_SEND) $<

clean:
	rm -f $(PROJ).json $(PROJ).asc $(PROJ).bin $(PROJ).uf2 $(PROJ)_*.log abc.history

%.ghw:
	$(GHDL) -c $(VHDL_FILES) $(TESTBENCH_FILES) -r $* --vcd=$*.vcd --wave=$@ --stop-time=$(SIM_TIME)

sim_show: $(SIM_ENTITY).ghw
	$(GTKWAVE) $<

sim_clean:
	rm -f $(SIM_ENTITY).ghw $(SIM_ENTITY).vcd

.SECONDARY:

.PHONY: all prog clean
