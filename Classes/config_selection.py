import os
import json
import numpy as np
import PySAM.TroughPhysicalIph as tpiph
import PySAM.LcoefcrDesign as lcoe
import PySAM.Utilityrate5 as utility
import PySAM.ThermalrateIph as tr
import PySAM.CashloanHeat as cl


class ConfigSelection:
    def __init__(self, config, selected_outputs, use_default = False):
        self.outputs_dict = {}
        self.selected_outputs = selected_outputs

        # the user does not need to know how SAM outputs are called internally
        self.output_name_map = {
            "LCOE": "lcoe_real",
            "NPV": "npv",
            "Payback": "payback",
            "Capacity Factor": "capacity_factor",
            "Savings": "savings_year1",
            # Add more if needed
        }
        self.config = config
        self.use_default = use_default
        if self.use_default:
            system_model = tpiph.default("PhysicalTroughIPHCommercial")
        else:
            system_model = tpiph.new()

        self.solar_field_group_object = getattr(system_model,'SolarField')
        self.TES_group_object = getattr(system_model,'TES')
        self.Controller_group_object = getattr(system_model,'Controller')

        cwd = os.getcwd()
        path = os.path.join(cwd, "JSON SAM Templates")

        match self.config:
            case "LCOH Calculator":
                finance_model = lcoe.from_existing(system_model)
                dir = path
                file_names = ["untitled_trough_physical_iph", "untitled_lcoefcr_design"]
                self.modules = [system_model, finance_model]

            case "Commercial owner":
                if self.use_default:
                    utility_model = utility.from_existing(system_model,"PhysicalTroughIPHCommercial")
                    thermalrate_model = tr.from_existing(system_model,"PhysicalTroughIPHCommercial")
                    financial_model = cl.from_existing(system_model)
                else:
                    utility_model = utility.from_existing(system_model)
                    thermalrate_model = tr.from_existing(system_model)
                    financial_model = cl.from_existing(system_model)
                dir = os.path.join(path,'Commercial_owner','')
                file_names = ["untitled_trough_physical_iph", "untitled_utilityrate5", "untitled_thermalrate_iph", "untitled_cashloan_heat"]
                self.modules = [system_model, utility_model, thermalrate_model, financial_model]


        if not self.use_default:
            for f, m in zip(file_names, self.modules):
                with open(dir + f + ".json", 'r') as file:
                    data = json.load(file)
                    # loop through each key-value pair
                    for k, v in data.items():
                        if k != "number_inputs":
                            try:
                                m.value(k, v)
                            except:
                                print("Not recognized key: " + k)
    
    """     def _collect_outputs(self):
            self.outputs_dict = {}
            for module in self.modules:
                if hasattr(module, "Outputs"):
                    outputs_group = getattr(module, "Outputs")
                    for attr in dir(outputs_group):
                        if not attr.startswith("_"):
                            try:
                                value = getattr(outputs_group, attr)
                                if not callable(value):
                                    self.outputs_dict[attr] = value
                            except RuntimeError as e:
                                # Handle PySAM's unassigned output
                                print(f"Output '{attr}' not available in module {module.__class__.__name__}: {e}")
                            except Exception as e:
                                print(f"Unexpected error retrieving '{attr}': {e}") """
    
    def _collect_outputs(self):
        outputs = []
        for key in self.selected_outputs:
            internal_key = self.output_name_map.get(key, key)
            found = False
            for module in self.modules:
                if hasattr(module, "Outputs"):
                    outputs_group = getattr(module, "Outputs")
                    if hasattr(outputs_group, internal_key):
                        try:
                            value = getattr(outputs_group, internal_key)
                            if not callable(value):
                                outputs.append(value)
                                found = True
                                break
                        except Exception as e:
                            print(f"Error retrieving '{internal_key}': {e}")
            if not found:
                print(f"Warning: Output '{internal_key}' not found in any module.")
        return np.array(outputs)
    
    def get_modules(self):
        return self.modules
    
    def sim_func(self, x):
        #setattr(self.solar_field_group_object, 'I_bn_des', x["I_bn_des"] )
        setattr(self.Controller_group_object, 'specified_solar_multiple', x["specified_solar_multiple"] )
        setattr(self.solar_field_group_object, 'T_loop_out', x["T_loop_out"] )
        setattr(self.TES_group_object, 'tshours', x["tshours"] )
        #setattr(TES_group_object, 'h_tank_in', x["h_tank_in"] )

        for m in self.modules:
            m.execute(1)

        # collect and return outputs after execution
        return self._collect_outputs()
    