# examples/opt3_subsystem_azimuth.py
"""
Subsystem optimization: Field azimuth only (flat site, slope = 0°)
Objectives: minimize PBT, maximize SF (via "-SF")
Design fixed to previously selected global design (Candidate A).
"""

from sammoo import ConfigSelection, ParMOOSim
from sammoo.components import ThermalLoadProfileLPG

# Optional land-use constraint (kept for consistency)
ENABLE_LAND_CONSTRAINT = True
MAX_LAND_AC = 1.0
constraints_dict = {"total_land_area": MAX_LAND_AC} if ENABLE_LAND_CONSTRAINT else {}

# Monthly LPG consumption data (kg) -> build hourly thermal load
monthly_data = {
    1: 11343,  2: 15133,  3: 4983,
    4: 13221,  5: 7250,   6: 12137,
    7: 8055,   8: 7542,   9: 7605,
    10: 12899, 11: 6090,  12: 12343
}
profile = ThermalLoadProfileLPG(monthly_kg=monthly_data)

# Decision variable: field azimuth only (0° = N-S, 90° = E-W)
design_variables = {
    "azimuth": ([0.0, 90.0], "continuous"),
}

# Objectives: minimize PBT, maximize SF (negated for minimization)
objective_functions = ["LCOE", "-SF"]

config = ConfigSelection(
    config="Commercial owner",
    selected_outputs=objective_functions,
    design_variables=design_variables,
    collector_name="NEP PolyTrough 1800",
    htf_name="Therminol VP-1",
    storage_fluid_name="Therminol VP-1",
    verbose=1,
    constraints_dict=constraints_dict,
)

# Fix the global design to Candidate A
config.set_inputs({
    "tshours": 19,
    "specified_solar_multiple": 3.155,
    "T_loop_out": 224.0,
    "n_sca_per_loop": 41,
    "Row_Distance": 4.766,
})

# Apply thermal load profile (injects q_pb_design and timestep_load_abs)
profile.apply_to_config(config)

# Run the MOOP
my_moop = ParMOOSim(config, search_budget=5)
my_moop.solve_all(sim_max=20)

# Results
results = my_moop.get_results()
print("Pareto (azimuth) with objectives [PBT, -SF]:")
print(results)
