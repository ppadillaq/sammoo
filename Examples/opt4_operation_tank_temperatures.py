# examples/opt4_operation_tank_temperatures.py

"""
Multi-objective optimization of cold and hot tank set temperatures 
for operational performance of the SHIP plant. 
Objectives: minimize LCOE and maximize SF.
"""

from sammoo import ConfigSelection, ParMOOSim
from sammoo.components import ThermalLoadProfileLPG
import numpy as np

# -----------------------------
# Toggle land-area constraint
# -----------------------------
ENABLE_LAND_CONSTRAINT = True
MAX_LAND_AC = 1.0  # adjust as needed

constraints_dict = {"total_land_area": MAX_LAND_AC} if ENABLE_LAND_CONSTRAINT else {}

# -----------------------------
# Monthly LPG consumption data (kg)
# -----------------------------
monthly_data = {
    1: 11343,  2: 15133,  3: 4983,
    4: 13221,  5: 7250,   6: 12137,
    7: 8055,   8: 7542,   9: 7605,
    10: 12899, 11: 6090,  12: 12343
}

# -----------------------------
# Generate thermal load profile
# -----------------------------
profile = ThermalLoadProfileLPG(monthly_kg=monthly_data)



# design_variables = {
#     "T_startup": ([150.0, 160.0], "continuous"),
#     "T_shutdown": ([150.0, 160.0], "continuous")
# }

# -----------------------------
# Define design space
# -----------------------------
design_variables = {
    "cold_tank_Thtr": ([40.0, 90.0], "continuous"),
    "hot_tank_Thtr": ([100.0, 200.0], "continuous")
}

# -----------------------------
# Define objective functions
# -----------------------------
selected_outputs = ["LCOE", "-SF"] # Minimize LCOE, maximize SF via -SF

# ------------------------
# Model configuration
# ------------------------
config = ConfigSelection(
    config="Commercial owner",
    selected_outputs=selected_outputs,
    design_variables=design_variables,
    collector_name="NEP PolyTrough 1800",
    htf_name="Therminol VP-1",
    storage_fluid_name="Therminol VP-1",
    verbose=1,
    constraints_dict=constraints_dict,
)

# Fix the global design to Candidate A
config.set_inputs({
    "tshours": 19,                    # Thermal energy storage duration [h]
    "specified_solar_multiple": 3.155,# Solar multiple (design capacity multiplier)
    "T_loop_out": 224.0,              # Loop outlet temperature [°C]
    "n_sca_per_loop": 41,
    "Row_Distance": 4.766,
})

# Apply demand profile → sets timestep_load_abs, q_pb_design and system_capacity
profile.apply_to_config(config)

# Initialize and solve optimization problem
moop = ParMOOSim(config, search_budget=10)
moop.solve_all(sim_max=50)

# Show results
results = moop.get_results()
print(results)
