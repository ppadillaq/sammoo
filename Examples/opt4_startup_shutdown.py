# examples/opt4_startup_shutdown.py


from sammoo import ConfigSelection, ParMOOSim
import numpy as np

# ------------------------
# Definición de variables
# ------------------------

design_variables = {
    "T_startup": ([170.0, 210.0], "continuous"),
    "T_shutdown": ([60.0, 100.0], "continuous")
}

# Objetivos a optimizar
# - LCOE debe minimizarse
# - Energy (negativo para maximizar)
selected_outputs = ["LCOE", "-annual_energy"]

# ------------------------
# Configuración del modelo
# ------------------------

config = ConfigSelection(
    config="Commercial owner",
    selected_outputs=selected_outputs,
    design_variables=design_variables,
    use_default=True,
    htf_name="Pressurized Water"
)

# Fijar consigna de temperaturas del campo solar
config.set_input("T_loop_out", 200.0)
config.set_input("T_loop_in", 90.0)

# ------------------------
# Ejecutar optimización
# ------------------------

moop = ParMOOSim(config, search_budget=40)
moop.solve_all(sim_max=1)

# ------------------------
# Mostrar resultados
# ------------------------

results = moop.get_results()
print(results)
