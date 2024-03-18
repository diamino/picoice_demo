library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity pll is
port(
	clock_in: in std_logic;
	clock_out: out std_logic;
	locked: out std_logic
	);
end entity pll;

architecture behav of pll is

	component SB_PLL40_PAD is 
		generic (
			FEEDBACK_PATH : String := "SIMPLE";
			DIVR : unsigned(3 downto 0) := "0000";
			DIVF : unsigned(6 downto 0) := "1001111";
			DIVQ : unsigned(2 downto 0) := "100";
			FILTER_RANGE : unsigned(2 downto 0) := "001"
		);
		port (
			PACKAGEPIN: in std_ulogic;
			PLLOUTCORE: out std_ulogic;
			LOCK: out std_ulogic;
			RESETB: in std_ulogic;
			BYPASS: in std_ulogic
		);
	end component;
 
begin

	SO_pll_inst: SB_PLL40_PAD
		port map(
			PACKAGEPIN => clock_in,
			PLLOUTCORE => clock_out,
			LOCK => locked,
			RESETB => '1',
			BYPASS => '0'
		);

end architecture behav;
