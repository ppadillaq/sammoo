# examples/opt4_startup_shutdown.py


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

# ------------------------
# Definición de variables
# ------------------------

# design_variables = {
#     "T_startup": ([150.0, 160.0], "continuous"),
#     "T_shutdown": ([150.0, 160.0], "continuous")
# }

design_variables = {
    "cold_tank_Thtr": ([50.0, 90.0], "continuous"),
    "hot_tank_Thtr": ([100.0, 170.0], "continuous")
}

# Objetivos a optimizar
# - LCOE debe minimizarse
# - Energy (negativo para maximizar)
selected_outputs = ["LCOE", "-SF"]

# ------------------------
# Configuración del modelo
# ------------------------

config = ConfigSelection(
    config="Commercial owner",
    selected_outputs=selected_outputs,
    design_variables=design_variables,
    collector_name="Absolicon T160",
    htf_name="Therminol VP-1",
    storage_fluid_name="Therminol VP-1",
    verbose=0,
    constraints_dict=constraints_dict,
)

# Apply demand profile → sets timestep_load_abs, q_pb_design and system_capacity
profile.apply_to_config(config)

# Set plant design point (fixed thermal capacity scenario)
config.set_inputs({
    "tshours": 5,                    # Thermal energy storage duration [h]
    "T_loop_out": 210.0,             # Loop outlet temperature [°C]
    "specified_solar_multiple": 1.8, # Solar multiple (design capacity multiplier)
    "n_sca_per_loop": 18,
})

# ------------------------
# Ejecutar optimización
# ------------------------

moop = ParMOOSim(config, search_budget=50)
moop.solve_all(sim_max=200)

# ------------------------
# Mostrar resultados
# ------------------------

results = moop.get_results()
print(results)
