# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.1.0]: https://github.com/ppadillaq/sammoo/releases/tag/v0.1.0

