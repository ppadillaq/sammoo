import numpy as np

import sys
sys.path.append(".")

from Classes.config_selection import ConfigSelection
from Classes.parmoo_simulation import ParMOOSim

config = ConfigSelection("Commercial owner")
modules = config.get_modules()
[system_model, utility_model, thermalrate_model, cashloan_model] = modules

designVariables = {"tshours": [2,15],
                   "I_bn_des": [800,1100],
                   "T_loop_out":[200,400]}
# "tshours", # hours of storage at design point
#"I_bn_des", # solar irradiation at design
# "T_loop_out", # Target loop outlet temperature [C]
# "h_tank_in" 'lb': 10, 'ub': 20} # total height of tank

def f1(x, s): return s["SAMOptim"][0]
def f2(x, s): return s["SAMOptim"][1]
objFunctions = {"payback": f1,
                "savings": f2}


# def field_optim_func(x):
#    Row_Distance = x["Row_Distance"]
#    solar_field_group_object = getattr(system_model,'SolarField')
#    setattr(solar_field_group_object, 'Row_Distance', Row_Distance )
#    return sx

def sim_func(x):

   solar_field_group_object = getattr(system_model,'SolarField')
   setattr(solar_field_group_object, 'I_bn_des', x["I_bn_des"] )
   setattr(solar_field_group_object, 'T_loop_out', x["T_loop_out"] )

   TES_group_object = getattr(system_model,'TES')
   setattr(TES_group_object, 'tshours', x["tshours"] )
   #setattr(TES_group_object, 'h_tank_in', x["h_tank_in"] )

   for m in modules:
      m.execute(1)

   #print('CF: ', system_model.Outputs.capacity_factor)
   #print('LCOE: ', finance_model.Outputs.lcoe_fcr)
   #CF = system_model.Outputs.capacity_factor
   payback = cashloan_model.Outputs.payback
   npv = cashloan_model.Outputs.npv
   #LCOE = cashloan_model.Outputs.lcoe_real
   #LCOE = finance_model.Outputs.lcoe_fcr
   #sx = np.array([-1*CF,LCOE])
   savings = utility_model.Outputs.savings_year1
   sx = np.array([payback,savings])
   return sx

my_moop = ParMOOSim(sim_func, designVariables, objFunctions)
my_moop.solve()