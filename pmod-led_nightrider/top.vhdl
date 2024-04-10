library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity top is
  port (
    clk : in std_logic;
    led_o: out std_logic_vector(7 downto 0)
  );

end top;

architecture behav of top is
  signal nrst, rst : std_logic := '0';
  signal leds : std_logic_vector(7 downto 0);
  signal pclk: std_logic;

  type Dir_State_Type is (left, right);
  signal dir_state: Dir_State_Type := left; 

begin
  
  prescaler_inst : entity work.prescaler
    generic map (
      factor  => 1_000_000 -- 12MHz/12Hz = 1_000_000
    )
    port map (
      clk_i   => clk,
      pclk_o  => pclk
    );

  -- Reset signal generation
  process (clk)
    variable cnt : unsigned (1 downto 0) := "00";
  begin
    if rising_edge (clk) then
      if cnt = 3 then
        nrst <= '1';
      else
        cnt := cnt + 1;
      end if;
    end if;
  end process;

  process (clk)
    variable leds: std_logic_vector(7 downto 0) := (others => '1');
  begin
    if rst = '1' then
      leds := "11111110";
      dir_state <= left; 
    elsif rising_edge(clk) then
      if pclk = '1' then
        case dir_state is
          when left =>
            leds := leds(6 downto 0) & '1'; 
            if leds(7) = '0' then
              dir_state <= right;
            end if;
          when right =>
            leds := '1' & leds(7 downto 1);
            if leds(0) = '0' then
              dir_state <= left;
            end if;
        end case;
      end if;
    end if;
    led_o <= std_logic_vector(leds);
  end process;

  -- led_o <= leds;

  rst <= not nrst;

end behav;