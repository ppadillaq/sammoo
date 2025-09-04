# examples/tes_timeseries_siph.py

from sammoo import ConfigSelection
from sammoo.components import ThermalLoadProfileLPG

import matplotlib.pyplot as plt

# Example monthly LPG consumption in kg
monthly_data = {
    1: 11343,  2: 15133,  3: 4983,
    4: 13221,  5: 7250,   6: 12137,
    7: 8055,   8: 7542,   9: 7605,
    10: 12899, 11: 6090,  12: 12343
}

design_variables = {"tshours": ([0,24],"integer"),                        # Thermal storage hours
                   "specified_solar_multiple": ([0.5,20.0],"continuous"),  # Solar multiple (SM)
                   "T_loop_out":([200,230],"integer"),                    # Loop outlet temperature [°C]
                   "n_sca_per_loop": ([7, 25], "integer"),                # SCAs per loop (discrete)
                   }      

# Single-point dictionary for sim_func
x = {
    "tshours": 6.0,
    "specified_solar_multiple": 1.8,
    "T_loop_out": 200.0,
    "n_sca_per_loop": 14
}

obj_functions = ["e_ch_tes"]
    # selected_outputs=[
    #     "time_hr", "e_ch_tes", "q_ch_tes", "q_dc_tes",
    #     "T_tes_hot", "T_tes_cold", "tank_losses"
    # ]

# Create configuration for SIPH with TES
config = ConfigSelection(
    config="Commercial owner",
    selected_outputs=obj_functions,
    design_variables=design_variables,
    collector_name="Power Trough 250",
    htf_name="Therminol VP-1",
    storage_fluid_name="Therminol VP-1",
    verbose=0,
)

# Apply thermal load profile
profile = ThermalLoadProfileLPG(monthly_kg=monthly_data)
profile.apply_to_config(config)

# Set design point inputs
config.set_inputs({
    "sim_type": 1,                  # timeseries
    "specified_solar_multiple": 15.0,
    "tshours": 24.0,
    "T_loop_out": 230.0,
    "n_sca_per_loop": 22
})

# Run the simulation and get TES time series
df = config.sim_func(x)

plt.plot(config.modules[0].value("e_ch_tes"))

# Save for inspection
#df.to_csv("tes_timeseries.csv", index=False)
#print("[INFO] TES time series saved to tes_timeseries.csv")
