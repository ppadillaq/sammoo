import sys
sys.path.append(".")

from Classes.config_selection import ConfigSelection
from Classes.parmoo_simulation import ParMOOSim

designVariables = {"tshours": ([0,20],"integer"),
                   "specified_solar_multiple": ([0.7,4.0],"continuous"),
                   "T_loop_out":([200,400],"integer")}

objFunctions = ["LCOE", "Payback","-LCS"]
config = ConfigSelection("Commercial owner", objFunctions, designVariables)
my_moop = ParMOOSim(config, search_budget=50)
my_moop.solve_all(sim_max=1)
results = my_moop.get_results()
print(results)