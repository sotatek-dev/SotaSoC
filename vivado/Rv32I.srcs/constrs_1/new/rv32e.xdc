# Configuration voltage properties
set_property CFGBVS VCCO [current_design]
set_property CONFIG_VOLTAGE 3.3 [current_design]

set_property PACKAGE_PIN R4 [get_ports clk_p]
set_property IOSTANDARD DIFF_SSTL15 [get_ports clk_p]

set_property PACKAGE_PIN R14 [get_ports rst_n]
set_property IOSTANDARD LVCMOS33 [get_ports rst_n]

create_clock -period 5.000 -name sys_clk [get_ports clk_p]

set_false_path -from [get_ports rst_n]

set_false_path -from [get_ports uart_rx]


set_property PACKAGE_PIN G18 [get_ports {ui_in[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {ui_in[0]}]
set_property PULLTYPE PULLDOWN [get_ports {ui_in[0]}]

set_property PACKAGE_PIN L18 [get_ports {ui_in[1]}]
set_property IOSTANDARD LVCMOS33 [get_ports {ui_in[1]}]

set_property PACKAGE_PIN M18 [get_ports {ui_in[2]}]
set_property IOSTANDARD LVCMOS33 [get_ports {ui_in[2]}]

set_property PACKAGE_PIN H22 [get_ports {ui_in[3]}]
set_property IOSTANDARD LVCMOS33 [get_ports {ui_in[3]}]

set_property PACKAGE_PIN J22 [get_ports {ui_in[4]}]
set_property IOSTANDARD LVCMOS33 [get_ports {ui_in[4]}]

set_property PACKAGE_PIN K22 [get_ports {ui_in[5]}]
set_property IOSTANDARD LVCMOS33 [get_ports {ui_in[5]}]

set_property PACKAGE_PIN G20 [get_ports {ui_in[6]}]
set_property IOSTANDARD LVCMOS33 [get_ports {ui_in[6]}]

set_property PACKAGE_PIN H20 [get_ports {ui_in[7]}]
set_property IOSTANDARD LVCMOS33 [get_ports {ui_in[7]}]


set_property PACKAGE_PIN H19 [get_ports {uo_out[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {uo_out[0]}]
set_property DRIVE 4 [get_ports {uo_out[0]}]

set_property PACKAGE_PIN F13 [get_ports {uo_out[1]}]
set_property IOSTANDARD LVCMOS33 [get_ports {uo_out[1]}]
set_property DRIVE 4 [get_ports {uo_out[1]}]

set_property PACKAGE_PIN A14 [get_ports {uo_out[2]}]
set_property IOSTANDARD LVCMOS33 [get_ports {uo_out[2]}]
set_property DRIVE 4 [get_ports {uo_out[2]}]

set_property PACKAGE_PIN C13 [get_ports {uo_out[3]}]
set_property IOSTANDARD LVCMOS33 [get_ports {uo_out[3]}]
set_property DRIVE 4 [get_ports {uo_out[3]}]

set_property PACKAGE_PIN G17 [get_ports {uo_out[4]}]
set_property IOSTANDARD LVCMOS33 [get_ports {uo_out[4]}]
set_property DRIVE 4 [get_ports {uo_out[4]}]

set_property PACKAGE_PIN L21 [get_ports {uo_out[5]}]
set_property IOSTANDARD LVCMOS33 [get_ports {uo_out[5]}]
set_property DRIVE 4 [get_ports {uo_out[5]}]

set_property PACKAGE_PIN M21 [get_ports {uo_out[6]}]
set_property IOSTANDARD LVCMOS33 [get_ports {uo_out[6]}]
set_property DRIVE 4 [get_ports {uo_out[6]}]

set_property PACKAGE_PIN H15 [get_ports {uo_out[7]}]
set_property IOSTANDARD LVCMOS33 [get_ports {uo_out[7]}]
set_property DRIVE 4 [get_ports {uo_out[7]}]

set_property PACKAGE_PIN B13 [get_ports {uio[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {uio[0]}]
set_property DRIVE 4 [get_ports {uio[0]}]
set_property SLEW SLOW [get_ports {uo_out[0]}]

set_property PACKAGE_PIN F14 [get_ports {uio[1]}]
set_property IOSTANDARD LVCMOS33 [get_ports {uio[1]}]
set_property DRIVE 4 [get_ports {uio[1]}]
set_property SLEW SLOW [get_ports {uo_out[1]}]

set_property PACKAGE_PIN D14 [get_ports {uio[2]}]
set_property IOSTANDARD LVCMOS33 [get_ports {uio[2]}]
set_property DRIVE 4 [get_ports {uio[2]}]
set_property SLEW SLOW [get_ports {uo_out[2]}]

set_property PACKAGE_PIN D16 [get_ports {uio[3]}]
set_property IOSTANDARD LVCMOS33 [get_ports {uio[3]}]
set_property DRIVE 4 [get_ports {uio[3]}]
set_property SLEW SLOW [get_ports {uo_out[3]}]

set_property PACKAGE_PIN J19 [get_ports {uio[4]}]
set_property IOSTANDARD LVCMOS33 [get_ports {uio[4]}]
set_property DRIVE 4 [get_ports {uio[4]}]
set_property SLEW SLOW [get_ports {uo_out[4]}]

set_property PACKAGE_PIN N22 [get_ports {uio[5]}]
set_property IOSTANDARD LVCMOS33 [get_ports {uio[5]}]
set_property DRIVE 4 [get_ports {uio[5]}]
set_property SLEW SLOW [get_ports {uo_out[5]}]

set_property PACKAGE_PIN M22 [get_ports {uio[6]}]
set_property IOSTANDARD LVCMOS33 [get_ports {uio[6]}]
set_property DRIVE 4 [get_ports {uio[6]}]
set_property SLEW SLOW [get_ports {uo_out[6]}]

set_property PACKAGE_PIN H17 [get_ports {uio[7]}]
set_property IOSTANDARD LVCMOS33 [get_ports {uio[7]}]
set_property DRIVE 4 [get_ports {uio[7]}]
set_property SLEW SLOW [get_ports {uo_out[7]}]


# set_input_delay -clock [get_clocks -of_objects [get_pins clk_ins/inst/mmcm_adv_inst/CLKOUT4]] -min -add_delay 0.500 [get_ports spi_miso]
# set_input_delay -clock [get_clocks -of_objects [get_pins clk_ins/inst/mmcm_adv_inst/CLKOUT4]] -max -add_delay 3.000 [get_ports spi_miso]

# set_output_delay -clock [get_clocks -of_objects [get_pins clk_ins/inst/mmcm_adv_inst/CLKOUT4]] -min -add_delay 0.500 [get_ports uart_tx]
# set_output_delay -clock [get_clocks -of_objects [get_pins clk_ins/inst/mmcm_adv_inst/CLKOUT4]] -max -add_delay 3.000 [get_ports uart_tx]
# set_output_delay -clock [get_clocks -of_objects [get_pins clk_ins/inst/mmcm_adv_inst/CLKOUT4]] -min -add_delay 0.000 [get_ports {gpio_out[*]}]
# set_output_delay -clock [get_clocks -of_objects [get_pins clk_ins/inst/mmcm_adv_inst/CLKOUT4]] -max -add_delay 3.000 [get_ports {gpio_out[*]}]

# set_output_delay -clock [get_clocks -of_objects [get_pins clk_ins/inst/mmcm_adv_inst/CLKOUT4]] -min -add_delay 0.500 [get_ports flash_cs_n]
# set_output_delay -clock [get_clocks -of_objects [get_pins clk_ins/inst/mmcm_adv_inst/CLKOUT4]] -max -add_delay 3.000 [get_ports flash_cs_n]
# set_output_delay -clock [get_clocks -of_objects [get_pins clk_ins/inst/mmcm_adv_inst/CLKOUT4]] -min -add_delay 0.500 [get_ports ram_cs_n]
# set_output_delay -clock [get_clocks -of_objects [get_pins clk_ins/inst/mmcm_adv_inst/CLKOUT4]] -max -add_delay 3.000 [get_ports ram_cs_n]
# set_output_delay -clock [get_clocks -of_objects [get_pins clk_ins/inst/mmcm_adv_inst/CLKOUT4]] -min -add_delay 0.500 [get_ports spi_mosi]
# set_output_delay -clock [get_clocks -of_objects [get_pins clk_ins/inst/mmcm_adv_inst/CLKOUT4]] -max -add_delay 3.000 [get_ports spi_mosi]


# set_property PACKAGE_PIN G17 [get_ports {uart_tx[0]}]
# set_property IOSTANDARD LVCMOS33 [get_ports {uart_tx[0]}]
# set_property DRIVE 4 [get_ports {uart_tx[0]}]

# set_property PACKAGE_PIN G18 [get_ports {uart_rx[0]}]
# set_property IOSTANDARD LVCMOS33 [get_ports {uart_rx[0]}]
# set_property PULLTYPE PULLDOWN [get_ports {uart_rx[0]}]

# set_property PACKAGE_PIN J19 [get_ports {gpio_out[0]}]
# set_property PACKAGE_PIN N22 [get_ports {gpio_out[1]}]
# set_property PACKAGE_PIN M22 [get_ports {gpio_out[2]}]
# set_property PACKAGE_PIN H17 [get_ports {gpio_out[3]}]
# set_property PACKAGE_PIN H18 [get_ports {gpio_out[4]}]
# set_property PACKAGE_PIN J15 [get_ports {gpio_out[5]}]
# set_property IOSTANDARD LVCMOS33 [get_ports {gpio_out[5]}]
# set_property IOSTANDARD LVCMOS33 [get_ports {gpio_out[4]}]
# set_property IOSTANDARD LVCMOS33 [get_ports {gpio_out[3]}]
# set_property IOSTANDARD LVCMOS33 [get_ports {gpio_out[2]}]
# set_property IOSTANDARD LVCMOS33 [get_ports {gpio_out[1]}]
# set_property IOSTANDARD LVCMOS33 [get_ports {gpio_out[0]}]
# set_property DRIVE 4 [get_ports {gpio_out[0]}]
# set_property DRIVE 4 [get_ports {gpio_out[1]}]
# set_property DRIVE 4 [get_ports {gpio_out[2]}]
# set_property DRIVE 4 [get_ports {gpio_out[3]}]
# set_property DRIVE 4 [get_ports {gpio_out[4]}]


# set_property PACKAGE_PIN G16 [get_ports {pwm_out[1]}]
# set_property PACKAGE_PIN J14 [get_ports {pwm_out[0]}]
# set_property IOSTANDARD LVCMOS33 [get_ports {pwm_out[1]}]
# set_property IOSTANDARD LVCMOS33 [get_ports {pwm_out[0]}]
# set_property DRIVE 4 [get_ports {pwm_out[0]}]
# set_property DRIVE 4 [get_ports {pwm_out[1]}]


# set_property DRIVE 4 [get_ports flash_cs_n]
# set_property DRIVE 4 [get_ports ram_cs_n]
# set_property DRIVE 4 [get_ports spi_sclk]


# set_property IOSTANDARD LVCMOS33 [get_ports error_flag]
# set_property PACKAGE_PIN H19 [get_ports error_flag]
# set_property DRIVE 4 [get_ports error_flag]



# External board
# set_property PACKAGE_PIN L20 [get_ports flash_cs_n]
# set_property IOSTANDARD LVCMOS33 [get_ports flash_cs_n]
# set_property PACKAGE_PIN H15 [get_ports ram_cs_n]
# set_property IOSTANDARD LVCMOS33 [get_ports ram_cs_n]
# set_property PACKAGE_PIN H22 [get_ports spi_sclk]
# set_property IOSTANDARD LVCMOS33 [get_ports spi_sclk]

# set_property PACKAGE_PIN J22 [get_ports {spi_io[0]}]
# set_property IOSTANDARD LVCMOS33 [get_ports {spi_io[0]}]
# set_property PACKAGE_PIN L19 [get_ports {spi_io[1]}]
# set_property IOSTANDARD LVCMOS33 [get_ports {spi_io[1]}]
# set_property PACKAGE_PIN K19 [get_ports {spi_io[2]}]
# set_property IOSTANDARD LVCMOS33 [get_ports {spi_io[2]}]
# set_property PACKAGE_PIN M18 [get_ports {spi_io[3]}]
# set_property IOSTANDARD LVCMOS33 [get_ports {spi_io[3]}]


#test1
# set_property PACKAGE_PIN F16 [get_ports flash_cs_n]
# set_property PACKAGE_PIN C18 [get_ports spi_sclk]

# set_property PACKAGE_PIN C19 [get_ports {spi_io[0]}]
# set_property IOSTANDARD LVCMOS33 [get_ports {spi_io[0]}]
# set_property DRIVE 4 [get_ports {spi_io[0]}]
# set_property PACKAGE_PIN E17 [get_ports {spi_io[1]}]
# set_property IOSTANDARD LVCMOS33 [get_ports {spi_io[1]}]
# set_property DRIVE 4 [get_ports {spi_io[1]}]
# set_property PACKAGE_PIN F18 [get_ports {spi_io[2]}]
# set_property IOSTANDARD LVCMOS33 [get_ports {spi_io[2]}]
# set_property DRIVE 4 [get_ports {spi_io[2]}]
# set_property PACKAGE_PIN C17 [get_ports {spi_io[3]}]
# set_property IOSTANDARD LVCMOS33 [get_ports {spi_io[3]}]
# set_property DRIVE 4 [get_ports {spi_io[3]}]


#test2
# set_property PACKAGE_PIN F13 [get_ports flash_cs_n]
# set_property IOSTANDARD LVCMOS33 [get_ports flash_cs_n]
# set_property PACKAGE_PIN A14 [get_ports ram_cs_n]
# set_property IOSTANDARD LVCMOS33 [get_ports ram_cs_n]
# set_property PACKAGE_PIN C13 [get_ports spi_sclk]
# set_property IOSTANDARD LVCMOS33 [get_ports spi_sclk]

# set_property PACKAGE_PIN B13 [get_ports {spi_io[0]}]
# set_property IOSTANDARD LVCMOS33 [get_ports {spi_io[0]}]
# set_property DRIVE 4 [get_ports {spi_io[0]}]
# set_property PACKAGE_PIN F14 [get_ports {spi_io[1]}]
# set_property IOSTANDARD LVCMOS33 [get_ports {spi_io[1]}]
# set_property DRIVE 4 [get_ports {spi_io[1]}]
# set_property PACKAGE_PIN D14 [get_ports {spi_io[2]}]
# set_property IOSTANDARD LVCMOS33 [get_ports {spi_io[2]}]
# set_property DRIVE 4 [get_ports {spi_io[2]}]
# set_property PACKAGE_PIN D16 [get_ports {spi_io[3]}]
# set_property IOSTANDARD LVCMOS33 [get_ports {spi_io[3]}]
# set_property DRIVE 4 [get_ports {spi_io[3]}]

# set_property SLEW SLOW [get_ports {spi_io[1]}]
# set_property SLEW SLOW [get_ports {spi_io[2]}]
# set_property SLEW SLOW [get_ports {spi_io[3]}]
# set_property SLEW SLOW [get_ports {spi_io[0]}]

