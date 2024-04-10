----------------------------------------------------------------------------------
-- Company: Diamino
-- Engineer: Diamino
-- 
-- Create Date:    24/12/2020 
-- Design Name: 
-- Module Name:    prescaler - Behavioral 
-- Project Name: 
-- Target Devices: 
-- Tool versions: 
-- Description: 
--
-- Dependencies: 
--
-- Revision: 
-- Revision 0.01 - File Created
-- Additional Comments: 
--
----------------------------------------------------------------------------------
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity prescaler is
    Generic (
        factor : integer := 2
    );
    Port (
        clk_i  : in  std_logic;
        pclk_o : out std_logic
    );
end prescaler;

architecture Behavioral of prescaler is

begin

    process (clk_i)
        variable counter: integer range 0 to factor := 0;
    begin
        if rising_edge(clk_i) then
            pclk_o <= '0';
            counter := counter + 1;
            if counter = factor then
                pclk_o <= '1';
                counter := 0;
            end if;
        end if;
    end process;

end Behavioral;
