# sam-model-optim

Optimization of Solar Industrial Process Heat (SIPH) systems using Concentrated Solar Power (CSP) technologies through the NREL [PySAM](https://nrel-pysam.readthedocs.io/en/latest/) package (System Advisor Model). This project was developed in the context of my Master's Thesis in Research in Industrial Technologies at the Universidad Nacional de Educación a Distancia (UNED), Spain.


---

## 🌞 Overview

This Python package integrates:
- **System Advisor Model (SAM)** via NREL PySAM for the simulation of parabolic trough systems.
- **ParMOO** for multi-objective optimization using surrogate models.

It allows you to:
- Run parametric studies on industrial CSP systems.
- Optimize system configurations with multiple economic and technical objectives.
- Analyze Pareto fronts and export results.

## 📦 Features

- Modular simulation wrapper (`ConfigSelection`) for different SAM configurations.
- Integration with PySAM modules: `TroughPhysicalIph`, `LcoefcrDesign`, `CashloanHeat`, etc.
- Multi-objective optimization engine (`ParMOOSim`) using ParMOO.
- Automatic switching from sequential to batch acquisition.
- Exportable plots and CSV reports.

## 🗂️ Project Structure


sam-model-optim/
├── samsimopt/ # Core package
│ ├── init.py
│ ├── config.py # Contains ConfigSelection class
│ ├── optimizer.py # Contains ParMOOSim class
│ └── templates/ # JSON SAM templates
│ └── *.json
├── examples/ # Example usage scripts
│ └── run_example.py
├── README.md
├── pyproject.toml
├── MANIFEST.in



---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/sam-model-optim.git
cd sam-model-optim
```

### 2. Install in editable mode

```
pip install -e .
```

### 3. Run an example

```
python examples/run_example.py
```

## 🛠 Dependencies

- Python ≥ 3.8
- NREL PySAM
- ParMOO
- NumPy
- Matplotlib (for plotting)

Install them via:

```
pip install pysam parmoo numpy matplotlib
```

## 📈 Example Use Case

```
from samsimopt import ConfigSelection, ParMOOSim

design_vars = {
    "specified_solar_multiple": [(1.0, 3.0), "float"],
    "tshours": [(2, 8), "int"]
}

selected_outputs = ["LCOE", "-NPV"]

cfg = ConfigSelection(
    config="Commercial owner",
    selected_outputs=selected_outputs,
    design_variables=design_vars
)

opt = ParMOOSim(cfg, auto_switch=True)
opt.optimize_step()
opt.plot_results()
```

## 📚 Publications

The version **1.0.0** of this project was submitted as part of the following Master's Thesis:

- Pedro Padilla Quesada. *Optimization of Solar Industrial Process Heat (SIPH) Systems with Parabolic Troughs using PySAM and Multi-objective Optimization*. Master’s Thesis in Research in Industrial Technologies, Universidad Nacional de Educación a Distancia (UNED), Spain, 2025.

[Download full thesis (PDF)](link_to_pdf_if_any)

Future versions may include broader support for other CSP technologies, reinforcement learning-based controllers, and integration with digital twin platforms.


## 📄 License
MIT License

## 👤 Author
Pedro Padilla Quesada
Master’s in Research in Industrial Technologies
UNED, Spain

