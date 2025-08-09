# weather_design_point.py
import re
import numpy as np
import pandas as pd
from datetime import datetime

class WeatherDesignPoint:
    """
    Computes I_bn_des (design-point DNI) as the DNI at solar noon
    on the summer solstice (June 21 in the northern hemisphere,
    December 21 in the southern hemisphere).
    """

    def __init__(self, weather_csv_path, verbose=1):
        self.path = weather_csv_path
        self.verbose = verbose
        self.lat, self.lon, self.tz = self._read_metadata(weather_csv_path)

    # ---------- Public API ----------
    def compute_I_bn_des(self, strategy="nearest_noon", window_minutes=60):
        """
        Compute I_bn_des using the weather file.

        Parameters
        ----------
        strategy : str
            'nearest_noon' -> take the sample with solar time closest to 12:00
            'max_window'   -> take the maximum DNI within ±window_minutes/2 around 12:00 solar time
        window_minutes : int
            Window width in minutes for 'max_window' strategy.

        Returns
        -------
        dni_value : float
            Design-point DNI in W/m².
        ts_local : pd.Timestamp
            Local time corresponding to the selected value.
        """
        df, dt_col, dni_col = self._load_df(self.path)
        year = int(df[dt_col].dt.year.mode().iat[0])  # dominant year (typical in TMY files)
        hemi = "north" if (self.lat is None or self.lat >= 0) else "south"
        mm, dd = (6, 21) if hemi == "north" else (12, 21)

        # Filter data for the summer solstice
        mask = (df[dt_col].dt.month == mm) & (df[dt_col].dt.day == dd)
        day = df.loc[mask].copy()
        if day.empty:
            raise ValueError("No rows found for the solstice in the weather file.")

        doy = int(datetime(year, mm, dd).timetuple().tm_yday)
        offset_min = self._solar_noon_offset_minutes(self.lon or 0.0, self.tz, doy)

        # Solar time in minutes from midnight
        local_mins = day[dt_col].dt.hour * 60 + day[dt_col].dt.minute
        solar_mins = local_mins + offset_min

        if strategy == "nearest_noon":
            idx = (np.abs(solar_mins - 720.0)).astype(float).idxmin()
            dni = float(day.loc[idx, dni_col])
            ts_local = day.loc[idx, dt_col]
        else:  # 'max_window'
            half = window_minutes / 2.0
            sel = day.loc[(solar_mins >= 720.0 - half) & (solar_mins <= 720.0 + half)]
            if sel.empty:
                idx = (np.abs(solar_mins - 720.0)).astype(float).idxmin()
                sel = day.loc[[idx]]
            k = sel[dni_col].astype(float).idxmax()
            dni = float(sel.loc[k, dni_col])
            ts_local = sel.loc[k, dt_col]

        if self.verbose:
            print(f"[INFO] I_bn_des={dni:.1f} W/m² @ {ts_local} (hemisphere={hemi})")
        return dni, ts_local

    def assign_to(self, solar_field_group_object, **kwargs):
        """
        Compute I_bn_des and assign it to a PySAM SolarField group object.

        Parameters
        ----------
        solar_field_group_object : PySAM.SolarField
            The SolarField group object where I_bn_des should be set.
        kwargs : dict
            Passed to compute_I_bn_des().
        """
        dni, _ = self.compute_I_bn_des(**kwargs)
        solar_field_group_object.I_bn_des = dni
        return dni

    # ---------- Internal helpers ----------
    @staticmethod
    def _read_metadata(csv_path):
        """
        Read latitude, longitude, and time zone from the CSV header.
        Fallback: extract lat/lon from filename if available.
        """
        lat = lon = tz = None
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                header = [next(f) for _ in range(20)]
            for line in header:
                if "Latitude" in line and "," in line:
                    try: lat = float(line.split(",")[1].strip())
                    except: pass
                if "Longitude" in line and "," in line:
                    try: lon = float(line.split(",")[1].strip())
                    except: pass
                if "Time Zone" in line and "," in line:
                    try: tz = float(line.split(",")[1].strip())
                    except: pass
        except Exception:
            pass
        if (lat is None or lon is None):
            m = re.search(r"([-+]?\d+\.\d+)_([-+]?\d+\.\d+)", csv_path)
            if m:
                lat = float(m.group(1)); lon = float(m.group(2))
        return lat, lon, tz

    @staticmethod
    def _load_df(csv_path):
        """
        Load the weather file into a DataFrame and detect the DNI column and timestamp column.
        """
        df = pd.read_csv(csv_path, low_memory=False)
        df.columns = [c.strip() for c in df.columns]
        # Find DNI column
        dni_col = next((c for c in ["DNI","dni","Dni","Direct Normal Irradiance","Direct Normal"]
                        if c in df.columns), None)
        if dni_col is None:
            raise ValueError("No DNI column found in the weather file.")
        # Build datetime column
        dt_col = None
        if all(c in df.columns for c in ["Year","Month","Day","Hour"]):
            dt = pd.to_datetime(df[["Year","Month","Day","Hour"]].rename(columns={"Hour":"hour"}))
            df.insert(0, "__dt__", dt)
            dt_col = "__dt__"
        else:
            for c in ["Datetime","Time","DateTime","timestamp"]:
                if c in df.columns:
                    df[c] = pd.to_datetime(df[c])
                    dt_col = c
                    break
        if dt_col is None:
            raise ValueError("Could not construct timestamp (missing Year/Month/Day/Hour or datetime column).")
        return df, dt_col, dni_col

    @staticmethod
    def _equation_of_time_minutes(doy):
        """
        Equation of Time (Spencer) approximation in minutes.
        """
        B = 2 * np.pi * (doy - 81) / 364.0
        return 9.87*np.sin(2*B) - 7.53*np.cos(B) - 1.5*np.sin(B)

    @classmethod
    def _solar_noon_offset_minutes(cls, lon_deg, tz_hours, doy):
        """
        Total correction in minutes: equation of time + longitude correction.
        """
        eot = cls._equation_of_time_minutes(doy)
        if tz_hours is None:
            tz_hours = round(lon_deg / 15.0)
        Lst = 15.0 * tz_hours
        long_corr = 4.0 * (lon_deg - Lst)  # minutes
        return eot + long_corr
