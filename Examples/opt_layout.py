from Classes.config_selection import ConfigSelection

config = ConfigSelection("Commercial owner")
modules = config.get_modules()

for m in modules:
      m.execute(1)

system_model = modules[0]
SolarField_group_object = getattr(system_model,'SolarField')

modules[3].Outputs.lcoe_nom

# In SAM GUI, number of loops is an output, but in PySAM you can set L_aperture
# Solar Field parameters
SolarField_group_object.T_startup # Startup temperature
SolarField_group_object.T_shutdown # Shutdown temperature
SolarField_group_object.Row_Distance # row spacing
SolarField_group_object.eta_pump # HTF pump efficiency
SolarField_group_object.azimuth # Azimuth angle of surface/axis [degrees]
# Solar Field outputs
system_model.Outputs.nLoops # number of loops

# Controller
Controller_group_object = getattr(system_model,'Controller')
Controller_group_object.specified_total_aperture


# System design point
SystemDesign_group_object = getattr(system_model,'SystemDesign')
SystemDesign_group_object.q_pb_design # Design heat input to power block [MWt]
SolarField_group_object.I_bn_des # Design point DNI
SolarField_group_object.T_loop_in_des # Design loop inlet temperature [C]
SolarField_group_object.T_loop_out # Target loop outlet temperature [C]
# outputs
system_model.Outputs.nameplate # Nameplate capacity [MWt]

# Thermal storage parameters
TES_group_object = getattr(system_model,'TES')
TES_group_object.d_tank_in # tank inner diameter (Required if is_h_tank_fixed=0|is_h_tank_fixed=2)
TES_group_object.tank_pairs # Parallel tank pairs
TES_group_object.store_fluid # Material number for storage fluid (required if tes_type=1)
TES_group_object.u_tank # Loss coefficient from the tank [W/m2-K]
TES_group_object.tshours # Equivalent full-load thermal storage hours [hr]
TES_group_object.cold_tank_max_heat # Rated heater capacity for cold tank heating [MWe]
# outputs
system_model.Outputs.csp_pt_tes_tank_diameter # Tank diameter [m]
system_model.Outputs.csp_pt_tes_tank_height # Tank height [m]
system_model.Outputs.q_dot_to_heat_sink # Actual Heat sink thermal power [MWt]
system_model.Outputs.q_tes # TES design capacity [MWht] = q_pb_design x tshours


# Collectors (SCAs)
SolarField_group_object.ColperSCA # Number of individual collector sections in an SCA 
SolarField_group_object.L_SCA # Length of the SCA [m] for the 4 types of collectors (tuple)
SolarField_group_object.L_aperture # Length of a single mirror/HCE unit [m]
# outputs
system_model.Outputs.nSCA # puede que sea a traves dif temp
system_model.Outputs.csp_dtr_sca_ap_lengths # Length of single module [m]


#system_model.value('specified_total_aperture',30000)
system_model.value('T_loop_out',150.0)
system_model.execute()
print(system_model.Outputs.nSCA)


# metrics
system_model.Outputs.heat_load_capacity_factor # Percentage of heat load met [%]