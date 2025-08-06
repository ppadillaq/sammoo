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


import pandas as pd
import matplotlib.pyplot as plt

class ThermalLoadProfileLPG:
    def __init__(self, monthly_kg, pci_kj_per_kg=46000, year=2019):
        """
        Initialize the ThermalLoadProfileLPG object.
        
        Parameters:
            monthly_kg (dict): Dictionary with month names (1-12) as keys and LPG mass in kg as values.
            pci_kj_per_kg (float): Lower heating value of LPG in kJ/kg (default 46,000 kJ/kg).
            year (int): Non-leap year for the time series.
        """
        self.monthly_kg = monthly_kg
        self.pci_kj_per_kg = pci_kj_per_kg
        self.year = year
        self.hourly_series = self._generate_hourly_series()

    def _generate_hourly_series(self):
        """Generate the hourly time series based on input data and working schedule."""
        dates = pd.date_range(start=f'{self.year}-01-01', end=f'{self.year}-12-31 23:00:00', freq='H')
        
        df = pd.DataFrame(index=dates)
        df['is_weekday'] = df.index.dayofweek < 5
        df['is_working_hour'] = (df.index.hour >= 6) & (df.index.hour < 19)
        df['active'] = df['is_weekday'] & df['is_working_hour']
        
        # Initialize energy series
        df['energy_kJ'] = 0.0
        
        for month, kg in self.monthly_kg.items():
            mask = (df.index.month == month) & df['active']
            active_hours = mask.sum()
            if active_hours > 0:
                total_energy_kJ = kg * self.pci_kj_per_kg
                hourly_energy = total_energy_kJ / active_hours
                df.loc[mask, 'energy_kJ'] = hourly_energy
        
        return df['energy_kJ']

    def plot_year(self):
        """Plot the yearly consumption profile (in kW or MW depending on peak value)."""
        power_series = self.hourly_series / 3600  # convert from kJ/h to kW
        peak_kw = power_series.max()

        if peak_kw > 1000:
            unit = "MW"
            values = power_series / 1000
        else:
            unit = "kW"
            values = power_series


        plt.figure(figsize=(15, 4))
        values.plot() # convert kJ/h to kW
        plt.xlabel("Date")
        plt.ylabel(f"Power ({unit})")
        plt.title(f"Hourly LPG Energy Consumption Profile ({unit})")
        plt.show()

    def plot_week(self, start_date=None):
        """
        Plots a weekly profile starting from the nearest Monday before the given date.
        Automatically scales to kW or MW depending on peak.
        
        Parameters:
            start_date (str or None): Any date string (YYYY-MM-DD). If None, defaults to first Monday of year.
        """
        if start_date is None:
            # Find first Monday of the year
            start = pd.Timestamp(f"{self.year}-01-01")
            start = start + pd.Timedelta(days=(7 - start.weekday()) % 7)
        else:
            start = pd.Timestamp(start_date)
            # Move back to Monday if not already Monday
            start = start - pd.Timedelta(days=start.weekday())
        
        end = start + pd.Timedelta(days=7)

        week_data = self.hourly_series.loc[(self.hourly_series.index >= start) & (self.hourly_series.index < end)] / 3600 # convert to kW

        peak_kw = week_data.max()
        if peak_kw > 1000:
            unit = "MW"
            values = week_data / 1000
        else:
            unit = "kW"
            values = week_data

        plt.figure(figsize=(15, 4))
        plt.plot(values.index, values.values, marker='o')
        plt.title(f"Weekly thermal load profile from {start.date()} to {end.date()} ({unit})")
        plt.xlabel("Datetime")
        plt.ylabel("Thermal load ({unit})")
        plt.grid(True)
        plt.show()

    def export_csv(self, filename="lpg_profile.csv"):
        """Export the hourly profile to a CSV file with energy in kJ, kWh, and power in kW."""
        df = self.hourly_series.to_frame(name='energy_kJ')
        df['energy_kWh'] = df['energy_kJ'] / 3600
        df['power_kW'] = df['energy_kWh']  # since it's per hour, energy and power are numerically the same
        df.to_csv(filename, header=True)
        print(f"[INFO] Hourly profile exported to {filename}")

    def print_summary(self):
        """Print total input and calculated totals by month for verification."""
        print("\n=== LPG Consumption Summary ===")
        input_totals = {month: kg * self.pci_kj_per_kg for month, kg in self.monthly_kg.items()}
        df = self.hourly_series.to_frame(name='energy_kJ')
        df['month'] = df.index.month
        calculated_totals = df.groupby('month')['energy_kJ'].sum()
        
        print(f"{'Month':<10} {'Input Energy (GJ)':>20} {'Calc. Energy (GJ)':>20}")
        for month in range(1, 13):
            input_gj = input_totals.get(month, 0) / 1e6
            calc_gj = calculated_totals.get(month, 0) / 1e6
            print(f"{month:<10} {input_gj:>20.3f} {calc_gj:>20.3f}")
        
        total_input = sum(input_totals.values()) / 1e6
        total_calc = calculated_totals.sum() / 1e6
        print(f"\n{'TOTAL':<10} {total_input:>20.3f} {total_calc:>20.3f}")
        
