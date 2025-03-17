

import sys
sys.path.append(".")

from Classes.config_selection import ConfigSelection
from Classes.parmoo_simulation import ParMOOSim

config = ConfigSelection("Commercial owner")
modules = config.get_modules()
[system_model, utility_model, thermalrate_model, cashloan_model] = modules

designVariables = {"tshours": ([2,15],"integer"),
                   "specified_solar_multiple": ([0.9,2.0],"continuous"),
                   "T_loop_out":([200,400],"integer")}
# "tshours", # hours of storage at design point
#"I_bn_des", # solar irradiation at design
# "T_loop_out", # Target loop outlet temperature [C]
# "h_tank_in" 'lb': 10, 'ub': 20} # total height of tank

def f1(x, s): return s["SAMOptim"][0]
def f2(x, s): return s["SAMOptim"][1]
objFunctions = {"LCOE": f1,
                "payback": f2}

# functions: -CF, LCOE, payback, savings

# def field_optim_func(x):
#    Row_Distance = x["Row_Distance"]
#    solar_field_group_object = getattr(system_model,'SolarField')
#    setattr(solar_field_group_object, 'Row_Distance', Row_Distance )
#    return sx

my_moop = ParMOOSim(config.sim_func, designVariables, objFunctions)
my_moop.solve()