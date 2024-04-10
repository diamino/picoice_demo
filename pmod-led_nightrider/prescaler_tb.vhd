library IEEE;
use IEEE.STD_LOGIC_1164.all;

entity prescaler_tb is
end entity;

architecture behaviour of prescaler_tb is

    component prescaler
        generic (
            factor      : integer
        );
    	port (
            clk_i		: in  std_logic;
            pclk_o      : out std_logic
	    );
    end component;

    signal clk      : std_logic := '0';
    signal pclk     : std_logic := '0';

    constant c_CLOCK_SPEED  : integer := 50_000_000;
    constant c_CLOCK_PERIOD : time := (1 * 1_000_000_000 / c_CLOCK_SPEED) * 1 ns;

begin

    -- instantiate Unit Under Test
    inst_uut : prescaler
        generic map (
            -- factor      => 2
            factor      => c_CLOCK_SPEED/44100
        )
        port map (
            clk_i       => clk,
            pclk_o      => pclk
        );

    clk <= not clk after c_CLOCK_PERIOD / 2;

end behaviour;