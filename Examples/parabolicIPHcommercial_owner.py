import sys
sys.path.append(".")

from Classes.config_selection import ConfigSelection
from Classes.parmoo_simulation import ParMOOSim

# "tshours", # hours of storage at design point
#"I_bn_des", # solar irradiation at design
# "T_loop_out", # Target loop outlet temperature [C]
# "h_tank_in" 'lb': 10, 'ub': 20} # total height of tank

#CF = self.modules[0].Outputs.capacity_factor
#LCOE = finance_model.Outputs.lcoe_fcr
#sx = np.array([-1*CF,LCOE])
#sx = np.array([LCOE,payback,-1*npv])

# objFunctions = {"LCOE": f1,
#                 "payback": f2,
#                 "-NPV": f3}

# functions: -CF, LCOE, payback, savings

# def field_optim_func(x):
#    Row_Distance = x["Row_Distance"]
#    solar_field_group_object = getattr(system_model,'SolarField')
#    setattr(solar_field_group_object, 'Row_Distance', Row_Distance )
#    return sx
designVariables = {"tshours": ([0,20],"integer"),
                   "specified_solar_multiple": ([0.7,3.5],"continuous"),
                   "T_loop_out":([200,400],"integer")}

objFunctions = ["LCOE", "Payback"]
config = ConfigSelection("Commercial owner", objFunctions, designVariables)
modules = config.get_modules()
[system_model, utility_model, thermalrate_model, cashloan_model] = modules

my_moop = ParMOOSim(config)
my_moop.solve_all(sim_max=1)