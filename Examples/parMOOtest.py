# examples/parMOOtest.py

import numpy as np

import sys
sys.path.append(".")

from sammoo import ConfigSelection, ParMOOSim

config = ConfigSelection("LCOH Calculator")
modules = config.get_modules()
[system_model, finance_model] = modules


def field_optim_func(x):
   Row_Distance = x["Row_Distance"]

   solar_field_group_object = getattr(system_model,'SolarField')
   setattr(solar_field_group_object, 'Row_Distance', Row_Distance )

   return sx

def sim_func(x):
   tshours = x["tshours"]
   #I_bn_des = x["I_bn_des"]
   h_tank = x["h_tank"]


   TES_group_object = getattr(system_model,'TES')
   setattr(TES_group_object, 'tshours', tshours )
   setattr(TES_group_object, 'h_tank', h_tank )

   for m in modules:
      m.execute(1)

   #print('CF: ', system_model.Outputs.capacity_factor)
   #print('LCOE: ', finance_model.Outputs.lcoe_fcr)
   CF = system_model.Outputs.capacity_factor
   LCOE = finance_model.Outputs.lcoe_fcr
   sx = np.array([-1*CF,LCOE])
   return sx


my_moop = ParMOOSim(sim_func, designVariables, objFunctions)
my_moop.solve()
