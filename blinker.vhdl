library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity blinker is
	port (
		clk : in std_logic;
		rst : in std_logic;
		out1, out2 : out std_logic
	);

end entity;

architecture rtl of blinker is
begin
	
	process (clk)
		variable count : unsigned (25 downto 0) := (others => '0');
	begin
		if rst = '1' then
			count := (others => '0');
		elsif rising_edge(clk) then
			out1 <= std_logic(count(25));
			out2 <= std_logic(count(8));
			count := count + 1;
		end if;
	end process;

end architecture rtl;