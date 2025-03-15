import os
import json
import PySAM.TroughPhysicalIph as tpiph
import PySAM.LcoefcrDesign as lcoe
import PySAM.Utilityrate5 as utility
import PySAM.ThermalrateIph as thermalrate
import PySAM.Cashloan as cashloan


class ConfigSelection:
    def __init__(self, config):
        self.config = config

    def get_modules(self):
        cwd = os.getcwd()
        path = os.path.join(cwd, "JSON SAM Templates")
        system_model = tpiph.new()
        match self.config:
            case "LCOH Calculator":
                finance_model = lcoe.from_existing(system_model)
                dir = path
                file_names = ["untitled_trough_physical_iph", "untitled_lcoefcr_design"]
                modules = [system_model, finance_model]

            case "Commercial owner":
                utility_model = utility.from_existing(system_model)
                thermalrate_model = thermalrate.from_existing(system_model)
                cashloan_model = cashloan.from_existing(system_model)
                dir = os.path.join(path,'Commercial_owner','')
                file_names = ["untitled_trough_physical_iph", "untitled_utilityrate5", "untitled_thermalrate_iph", "untitled_cashloan_heat"]
                modules = [system_model, utility_model, thermalrate_model, cashloan_model]


        for f, m in zip(file_names, modules):
            with open(dir + f + ".json", 'r') as file:
                data = json.load(file)
                # loop through each key-value pair
                for k, v in data.items():
                    if k != "number_inputs":
                        try:
                            m.value(k, v)
                        except:
                            print("Not recognized key: " + k)

        return modules
    