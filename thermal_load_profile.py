import pandas as pd
import numpy as np

year = 2025

hourly_ts = pd.Series(pd.date_range(start=f'{year}-01-01', end=f'{year}-12-31 23:00:00', freq='H'))

day_of_week = hourly_ts.dt.day_of_week

is_weekday = np.where(day_of_week < 5, True, False)

is_working_hour = np.where(hourly_ts.dt.hour > 6 and hourly_ts.dt.hour < 19, True, False)

#thermal_load = if weekday

#dates = pd.to_datetime({"year": df.Year, "month": df.Month, "day": df.Day})

print('')