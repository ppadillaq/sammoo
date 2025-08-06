# examples/lpg_usage.py

from sammoo.profiles.thermal_load_lpg import ThermalLoadProfileLPG


if __name__ == "__main__":
        monthly_data = {
            1: 11343,
            2: 15133,
            3: 4983,
            4: 13221,
            5: 7250,
            6: 12137,
            7: 8055,
            8: 7542,
            9: 7605,
            10: 12899,
            11: 6090,
            12: 12343
        }

        profile = ThermalLoadProfileLPG(monthly_data)
        profile.print_summary()
        profile.plot_year()
        profile.plot_week("2019-03-07")
        print(profile.get_average_power_mw())
        #profile.export_csv()