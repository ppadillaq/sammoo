# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-08-12

### Added
- **Collector data integration**:
  - New `iph_collectors_parameters.csv` database with parameters for parabolic-trough collectors specific to industrial process heat (IPH).
  - New `collector_name` parameter in `ConfigSelection` constructor to select a predefined collector from the database.
  - New internal methods `_load_collector_data()` and `_set_collector_inputs()` to automatically load and apply collector specifications.
  - `_set_collector_inputs()` now writes `L_aperture` automatically from `L_SCA` and `ColperSCA`.
- **HTF selection**:
  - Added `htf_name` parameter in `ConfigSelection` constructor with an internal dictionary mapping to PySAM fluid codes.
- New methods in `ThermalLoadProfileLPG`:
  - `get_average_power_mw()` – returns average load in MW.
  - `get_hourly_kw_profile()` – returns load in kW for direct use in SAM's `timestep_load_abs`.
  - `apply_to_config()` method in `ThermalLoadProfileLPG` to directly inject thermal load profiles into a `ConfigSelection` instance.
- Method `_estimate_installed_cost` in `ConfigSelection` to estimate total installation cost (used in `sim_func`).
- Optional verbosity control for SAM simulation runs (`verbose` parameter in `ConfigSelection`).
- Project logo added and referenced in README.
- New example: optimization of startup/shutdown temperatures.

### Changed
- Updated default JSON templates with refined design-point settings and collector parameters.
- Improved thermal load profile generation:
  - Added conversion efficiency (default 89%) and relevant unit conversions.
  - Updated `print_summary()` to show both chemical and useful energy.
- In `ParMOOSim.solve_all()`, plotting is now optional via `plot` parameter.
- Removed unintended modification of `system_capacity` in `CashloanHeat` configuration path.
- Refactored examples: cleaned naming, consolidated final set to:
  - `opt1_single_objective_comparison.py`
  - `opt2_design_point_multiobj.py`
  - `opt3_multiobj_row_distance.py`
  - `opt4_startup_shutdown.py`

### Fixed
- None.

## [0.1.0] - 2025-07-20
### Added
- Initial release of the `sammoo` Python package.
- `ConfigSelection` class to configure PySAM simulations from JSON templates.
- `ParMOOSim` class for multi-objective optimization using ParMOO.
- Support for the *Industrial Process Heat* + *Commercial Owner* configuration in SAM.
- Built-in JSON templates included under `sammoo/templates/iph_parabolic_commercial_owner/`.
- `ThermalLoadProfileLPG` class for generating hourly thermal load profiles from monthly LPG data.
- Added `sammoo.profiles.thermal_load_lpg` module to package structure.
- Example script: `examples/lpg_usage.py`.
- Example script: `examples/multiobj_row_distance_opt.py`.
- Example script: `examples/opt_layout.py`.
- Example script: `examples/parabolicIPHcommercial_owner.py`.
- Example script: `examples/single_objective_comparison.py`.
- Example script: `examples/test_utility_module.py`.

### Changed
- Nothing.

### Fixed
- Nothing.

[0.2.0]: https://github.com/ppadillaq/sammoo/releases/tag/v0.2.0
[0.1.0]: https://github.com/ppadillaq/sammoo/releases/tag/v0.1.0

