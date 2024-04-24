'''
Default Pico-ICE main module
'''
import icefpga
import picoice

NORMAL_BOOT_ENABLE = False
BOOT_WAIT = 15


def main():
    icefpga.ice_fpga_init(12)
    icefpga.ice_fpga_start()
    print("Ready to receive bitstream...")
    while True:
        picoice.wait_for_transmission(BOOT_WAIT)
        if NORMAL_BOOT_ENABLE:
            break

    print("Normal boot...")


if __name__ == '__main__':
    main()
