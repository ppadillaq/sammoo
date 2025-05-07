import sys
sys.path.append(".")

from Classes.config_selection import ConfigSelection
from Classes.parmoo_simulation import ParMOOSim

designVariables = {"tshours": ([0,20],"integer"),
                   "specified_solar_multiple": ([0.7,3.5],"continuous"),
                   "T_loop_out":([200,400],"integer")}

objFunctions = ["LCOE", "Payback"]
config = ConfigSelection("Commercial owner", objFunctions, designVariables)
modules = config.get_modules()
[system_model, utility_model, thermalrate_model, cashloan_model] = modules

my_moop = ParMOOSim(config)
my_moop.solve_all(sim_max=1)