# SPDX-License-Identifier: BSD-3-Clause
#
# Copyright (c) 2025, Pedro Padilla Quesada
# All rights reserved.
#
# This file is part of the sammoo project: a Python-based framework
# for multi-objective optimization of renewable energy systems using
# NREL's System Advisor Model (SAM).
#
# Distributed under the terms of the BSD 3-Clause License.
# For full license text, see the LICENSE file in the project root.


import json
import numpy as np
import PySAM.TroughPhysicalIph as tpiph
import PySAM.LcoefcrDesign as lcoe
import PySAM.Utilityrate5 as utility
import PySAM.ThermalrateIph as tr
import PySAM.CashloanHeat as cl

from importlib.resources import files


class ConfigSelection:
    def __init__(self, config, selected_outputs, design_variables, use_default = True, user_weather_file=None):
        """
        Initializes a configuration for a PySAM simulation.

        Parameters:
            config (str): 
                Configuration preset name. Supported options: "LCOH Calculator", "Commercial owner".
            selected_outputs (list of str): 
                List of objective functions to extract after simulation.
            design_variables (dict): 
                Dictionary of design variables, with bounds and types.
            use_default (bool, optional): 
                If True, loads PySAM modules with default technology configuration. Defaults to True.
            user_weather_file (str, optional): 
                Path to a user-provided weather CSV file. If None, a default internal file is used.
    
        Raises:
            ValueError: If required SAM templates or weather file are missing.
        """
        self.selected_outputs = selected_outputs
        self.design_variables = design_variables

        # the user does not need to know how SAM outputs are called internally
        self.output_name_map = {
            "LCOE": "lcoe_real",
            "-NPV": "npv",
            "Payback": "payback",
            "-Capacity Factor": "capacity_factor",
            "-Savings": "savings_year1",
            "CF": "capacity_factor",
            "utility_bill_wo_sys_year1": "utility_bill_wo_sys_year1",
            "utility_bill_w_sys_year1": "utility_bill_w_sys_year1",
            "annual_energy": "annual_energy",
            "-LCS": "cf_discounted_savings",
            # Add more if needed
        }
        #LCOE = finance_model.Outputs.lcoe_fcr

        self.config = config
        self.use_default = use_default
        if self.use_default:
            system_model = tpiph.default("PhysicalTroughIPHCommercial")
        else:
            system_model = tpiph.new()

        self.solar_field_group_object = getattr(system_model,'SolarField')
        self.TES_group_object = getattr(system_model,'TES')
        self.Controller_group_object = getattr(system_model,'Controller')

        self.variable_to_group = {
            "specified_solar_multiple": self.Controller_group_object,
            "I_bn_des": self.solar_field_group_object, # solar irradiation at design
            "T_loop_out": self.solar_field_group_object, # Target loop outlet temperature [C]
            "tshours": self.TES_group_object, # hours of storage at design point
            "h_tank_in": self.TES_group_object, # total height of tank 'lb': 10, 'ub': 20
            "Row_Distance": self.solar_field_group_object
        }

        match self.config:
            case "LCOH Calculator":
                finance_model = lcoe.from_existing(system_model)
                template_dir = files("sammoo.templates.iph_LCOH_calculator")
                file_names = ["untitled_trough_physical_iph", "untitled_lcoefcr_design"]
                self.modules = [system_model, finance_model]

            case "Commercial owner":
                if self.use_default:
                    utility_model = utility.from_existing(system_model,"PhysicalTroughIPHCommercial")
                    thermalrate_model = tr.from_existing(system_model,"PhysicalTroughIPHCommercial")
                    financial_model = cl.from_existing(system_model,"PhysicalTroughIPHCommercial")
                else:
                    utility_model = utility.from_existing(system_model)
                    thermalrate_model = tr.from_existing(system_model)
                    financial_model = cl.from_existing(system_model)
                template_dir = files("sammoo.templates.iph_parabolic_commercial_owner")
                file_names = [
                    "untitled_trough_physical_iph",
                    "untitled_utilityrate5",
                    "untitled_thermalrate_iph",
                    "untitled_cashloan_heat"
                    ]
                self.modules = [system_model, utility_model, thermalrate_model, financial_model]

        for f, m in zip(file_names, self.modules):
            json_path = template_dir.joinpath(f + ".json")
            with open(json_path, 'r') as file:
                data = json.load(file)
                # loop through each key-value pair
                for k, v in data.items():
                    if k != "number_inputs":
                        try:
                            m.value(k, v)
                        except:
                            print("Not recognized key: " + k)

        # 🔧 Weather file assignment logic
        try:
            if user_weather_file is not None:
                # 1. User provides their own weather file → highest priority
                self.modules[0].value("file_name", user_weather_file)
                print(f"[INFO] Using user-provided weather file: {user_weather_file}")
            else:
                # 2. Check if the template already included a valid file_name
                file_name = self.modules[0].value("file_name")
                if not file_name:
                    # If missing or empty → use default weather file
                    default_weather = self.get_default_weather_path()
                    self.modules[0].value("file_name", default_weather)
                    print(f"[INFO] No weather file found in template. Using default: {default_weather}")
                else:
                    print(f"[INFO] Using weather file from template: {file_name}")
        except Exception as e:
            print(f"[ERROR] Failed to assign weather file: {e}")
    
    def get_default_weather_path(self):
        """
        Returns the path to the default weather file included in the package.
        """
        try:
            weather_file = files("sammoo.resources.solar_resource").joinpath("tucson_az_32.116521_-110.933042_psmv3_60_tmy.csv")
            return str(weather_file)
        except Exception as e:
            raise FileNotFoundError(f"[ERROR] Default weather file not found: {e}")
    
    def get_input(self, key):
        for module in self.modules:
            try:
                return module.value(key)
            except Exception:
                continue
        print(f"[WARN] Input variable '{key}' not found.")
        return None
    
    def set_input(self, key, value):
        """
        Sets the value of any input parameter in the loaded PySAM modules.

        Parameters:
            key (str): The name of the input variable to set.
            value (any): The value to assign to the input variable.
        """
        found = False
        for module in self.modules:
            try:
                module.value(key, value)
                found = True
                break
            except Exception as e:
                module_name = module.__class__.__name__
                print(f"[DEBUG] Failed to set '{key}' in module '{module_name}': {e}")
                continue
        if not found:
            print(f"[WARN] Input variable '{key}' not found in any loaded module.")

    def set_inputs(self, inputs_dict):
        """
        Sets multiple input values at once from a dictionary.

        Parameters:
            inputs_dict (dict): Keys are input variable names, values are the values to assign.
        """
        for key, value in inputs_dict.items():
            self.set_input(key, value)
    
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
                                # Caso especial para LCS
                                if key == "-LCS" and isinstance(value, (list, tuple, np.ndarray)):
                                     outputs.append(value[-1])
                                else:
                                    outputs.append(value)
                                found = True
                                break
                        except Exception as e:
                            print(f"Error retrieving '{internal_key}': {e}")
            if not found:
                print(f"Warning: Output '{internal_key}' not found in any module.")
        return np.array(outputs)
    
    def set_debug_outputs(self, additional_outputs):
        """
        Appends extra outputs to the current list of selected outputs.

        This is useful for debugging or extended post-analysis,
        allowing you to retrieve variables that were not used as objectives
        during optimization but are still of interest.

        Parameters:
            additional_outputs (list of str): List of user-facing output names
                                            (as defined in output_name_map) to add.
        """
        # Combine current selected outputs with new ones, removing duplicates
        all_outputs = list(set(self.selected_outputs + additional_outputs))
        self.selected_outputs = all_outputs
        print(f"[INFO] selected_outputs updated to include {len(additional_outputs)} additional variables.")
    
    def get_modules(self):
        return self.modules
    
    def sim_func(self, x):
        try:
            for var_name in x:
                group_object = self.variable_to_group.get(var_name)
                if group_object is not None:
                    setattr(group_object, var_name, x[var_name])
                else:
                    print(f"Warning: Variable '{var_name}' not mapped to any group object")

            for m in self.modules:
                m.execute(1)

            # collect and return outputs after execution
            return self._collect_outputs()
        except Exception as e:
            print(f"[ERROR] Simulation failed for input {x} with error: {e}")
            return [np.nan] * len(self.selected_outputs)
    