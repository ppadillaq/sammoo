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
        Read latitude, longitude, and time zone from the first ~30 lines
        (works with comma- or tab-delimited headers). Falls back to lat/lon in filename.
        """
        import re
        lat = lon = tz = None
        try:
            with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
                header = [next(f) for _ in range(30)]
            def grab(pattern):
                for line in header:
                    m = re.search(pattern, line, re.IGNORECASE)
                    if m:
                        return float(m.group(1))
                return None
            lat = grab(r"Latitude[^\d\-+]*([\-+]?\d+(?:\.\d+)?)")
            lon = grab(r"Longitude[^\d\-+]*([\-+]?\d+(?:\.\d+)?)")
            tz  = grab(r"Time\s*Zone[^\d\-+]*([\-+]?\d+(?:\.\d+)?)")
        except Exception:
            pass
        if (lat is None or lon is None):
            m = re.search(r"([-+]?\d+\.\d+)[_,]([-+]?\d+\.\d+)", csv_path)
            if m:
                lat = float(m.group(1)); lon = float(m.group(2))
        return lat, lon, tz

    @staticmethod
    def _load_df(csv_path):
        """
        Load weather CSV supporting:
        1) NSRDB/PSM3 with 'Year,Month,Day,Hour[,Minute]'
        2) SAM/NSRDB classic with 'Date (MM/DD/YYYY), Time (HH:MM)' + units in headers

        Returns
        -------
        df : pd.DataFrame
        dt_col : str   # datetime column name
        dni_col : str  # DNI column name in df
        """
        import re
        import pandas as pd

        # ---- 1) Detect header row ----
        header_idx = None
        with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f):
                s = line.strip().lower()
                if s.startswith("year") or s.startswith("date"):
                    header_idx = i
                    break
        if header_idx is None:
            raise ValueError("Could not find header row starting with 'Year' or 'Date'.")

        # ---- 2) Read with auto-delimiter (comma or tab) ----
        df = pd.read_csv(csv_path, sep=None, engine="python", header=header_idx)
        orig_cols = list(df.columns)

        # Normalize names: drop units in parentheses, keep alphanumerics/space/_/-
        def normalize(name: str) -> str:
            base = re.sub(r"\(.*?\)", "", str(name))
            base = re.sub(r"[^A-Za-z0-9 _\-]", "", base)
            return base.strip().lower()

        norm_map = {c: normalize(c) for c in orig_cols}
        df.rename(columns=norm_map, inplace=True)

        # ---- 3) Find DNI column (be tolerant) ----
        dni_col = None
        for c in df.columns:
            cl = str(c).strip().lower()
            if cl == "dni" or cl.startswith("dni "):
                dni_col = c
                break
            if cl in ("direct normal irradiance", "direct normal"):
                dni_col = c
                break
        if dni_col is None:
            # Fallback: search original headers containing 'dni'
            for oc in orig_cols:
                if "dni" in str(oc).lower():
                    dni_col = norm_map[oc]
                    break
        if dni_col is None:
            raise ValueError("No DNI column found (tried 'DNI', 'Direct Normal Irradiance').")

        # ---- 4) Build datetime ----
        dt_col = "__dt__"

        # Case A: year/month/day/hour(/minute)
        if all(k in df.columns for k in ("year", "month", "day", "hour")):
            data = {
                "year":  df["year"].astype(int, errors="ignore"),
                "month": df["month"].astype(int, errors="ignore"),
                "day":   df["day"].astype(int, errors="ignore"),
                "hour":  df["hour"].astype(int, errors="ignore"),
            }
            if "minute" in df.columns:
                data["minute"] = df["minute"].astype(int, errors="ignore")
            else:
                data["minute"] = 0
            dt = pd.to_datetime(data, errors="coerce")
            if dt.isna().all():
                raise ValueError("Failed to assemble datetime from year/month/day/hour(/minute).")
            df.insert(0, dt_col, dt)
            return df, dt_col, dni_col

        # Case B: date/time columns (with units in original names)
        date_col = next((c for c in df.columns if c.startswith("date")), None)
        time_col = next((c for c in df.columns if c.startswith("time")), None)
        if date_col and time_col:
            # Try explicit format first; fall back to pandas parser
            dt = pd.to_datetime(df[date_col].astype(str) + " " + df[time_col].astype(str),
                                format="%m/%d/%Y %H:%M", errors="coerce")
            if dt.isna().any():
                dt = pd.to_datetime(df[date_col].astype(str) + " " + df[time_col].astype(str),
                                    errors="coerce")
            if dt.isna().all():
                raise ValueError("Failed to parse Date/Time columns into timestamps.")
            df.insert(0, dt_col, dt)
            return df, dt_col, dni_col

        # Case C: any existing datetime-like column
        for c in ("datetime", "time", "timestamp", "date"):
            if c in df.columns:
                df[c] = pd.to_datetime(df[c], errors="coerce")
                if df[c].notna().any():
                    return df, c, dni_col

        raise ValueError("Cannot construct timestamp: missing (Year/Month/Day/Hour) or (Date/Time).")


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
