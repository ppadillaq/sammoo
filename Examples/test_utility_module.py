import os
import json
import numpy as np
import PySAM.TroughPhysicalIph as tpiph
import PySAM.LcoefcrDesign as lcoe
import PySAM.Utilityrate5 as utility
import PySAM.ThermalrateIph as tr
import PySAM.CashloanHeat as cl

# --- Cargar todos los módulos desde archivos JSON ---
cwd = os.getcwd()
path = os.path.join(cwd, "JSON SAM Templates", "Commercial_owner", "")

system_model = tpiph.default("PhysicalTroughIPHCommercial")
thermalrate_model = tr.from_existing(system_model,"PhysicalTroughIPHCommercial")
utility_model = utility.from_existing(system_model,"PhysicalTroughIPHCommercial")
financial_model = cl.from_existing(system_model,"PhysicalTroughIPHCommercial")

file_names = [
    "untitled_trough_physical_iph",
    "untitled_utilityrate5",
    "untitled_thermalrate_iph",
    "untitled_cashloan_heat"
]
modules = [system_model, utility_model, thermalrate_model, financial_model]

for f, m in zip(file_names, modules):
    with open(os.path.join(path, f + ".json"), 'r') as file:
        data = json.load(file)
        for k, v in data.items():
            if k != "number_inputs":
                try:
                    m.value(k, v)
                except:
                    print(f"[WARN] Not recognized key: {k}")

# --- Añadir/forzar entradas necesarias a utility_model ---
#utility_model.value("analysis_period", 25)
utility_model.value("system_use_lifetime_output", 0)
#utility_model.value("gen", [0.5] * 8760)
#utility_model.value("inflation_rate", 2.5)
#utility_model.value("degradation", [0.5] * 25)


# --- Ejecutar todos los módulos ---
for m in modules:
    m.execute(1)

# --- Obtener los resultados deseados ---
outputs_group = utility_model.Outputs

# Suponiendo que ya has accedido a Outputs:
monthly = np.array(outputs_group.utility_bill_wo_sys_ym)
yearly = np.array(outputs_group.utility_bill_wo_sys)

# Comprobación
if np.allclose(monthly.sum(axis=1), yearly):
    print("✅ La suma mensual coincide con los totales anuales.")
else:
    print("❌ Hay discrepancias entre la suma mensual y los valores anuales.")
    print("Diferencias:", monthly.sum(axis=1) - yearly)

lcs = sum(np.array(outputs_group.utility_bill_wo_sys) - 
          np.array(outputs_group.utility_bill_w_sys))

try:
    bill_wo = outputs_group.utility_bill_wo_sys_year1
    print("utility_bill_wo_sys_year1:", bill_wo)
except AttributeError:
    print("[ERROR] 'utility_bill_wo_sys_year1' no disponible.")

try:
    bill_w = outputs_group.utility_bill_w_sys_year1
    print("utility_bill_w_sys_year1:", bill_w)
except AttributeError:
    print("[ERROR] 'utility_bill_w_sys_year1' no disponible.")