LIBRARY ieee;
USE ieee.std_logic_1164.ALL;
 
-- Uncomment the following library declaration if using
-- arithmetic functions with Signed or Unsigned values
--USE ieee.numeric_std.ALL;
 
ENTITY blinker_tb IS
END blinker_tb;
 
ARCHITECTURE behavior OF blinker_tb IS 
 
    -- Component Declaration for the Unit Under Test (UUT)
 
    COMPONENT blinker
    PORT(
         clk : in std_logic;
         rst : in std_logic;
         out1, out2 : out std_logic
        );
    END COMPONENT;

   --Inputs
   signal clk : std_logic := '0';
   signal rst : std_logic := '1';

 	--Outputs
   signal led1, led2 : std_logic;

   -- Clock period definitions
   constant clk12_period : time := 83 ns;
 
BEGIN
 
	-- Instantiate the Unit Under Test (UUT)
   uut: blinker PORT MAP (
          clk => clk,
          rst => rst,
          out1 => led1,
          out2 => led2
        );

   -- Clock process definitions
   clk12_process :process
   begin
		clk <= '0';
		wait for clk12_period/2;
		clk <= '1';
		wait for clk12_period/2;
   end process;
 

   -- Stimulus process
   stim_proc: process
   begin		
      -- hold reset state for 100 ns.
      wait for 100 ns;	
      rst <= '0';

      wait for clk12_period*10;

      -- insert stimulus here 

      wait;
   end process;

END;
