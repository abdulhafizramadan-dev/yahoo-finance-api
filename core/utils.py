import math


def serialize_value(v):
    try:
        if v is None:
            return None
        if isinstance(v, bool):
            return v
        if isinstance(v, int):
            return v
        if isinstance(v, float):
            if math.isnan(v) or math.isinf(v):
                return None
            return v
        if isinstance(v, str):
            return v
        if isinstance(v, list):
            return [serialize_value(item) for item in v]
        if isinstance(v, dict):
            return {k: serialize_value(val) for k, val in v.items()}
        try:
            import pandas as _pd
            import numpy as _np

            if isinstance(v, _pd.Timestamp):
                return v.isoformat()
            if isinstance(v, (_np.integer,)):
                return int(v)
            if isinstance(v, (_np.floating,)):
                f = float(v)
                return None if (math.isnan(f) or math.isinf(f)) else f
            if isinstance(v, _np.ndarray):
                return [serialize_value(item) for item in v.tolist()]
            try:
                if _pd.isna(v):
                    return None
            except Exception:
                pass
        except Exception:
            pass
        return str(v)
    except Exception:
        return str(v)


def serialize_df_to_records(df, index_key="period"):
    """
    Convert a yfinance analysis DataFrame (periods/dates as index, metrics as columns)
    to [{"period": "0q", "avg": 0.52, ...}, ...].
    Use index_key="date" when the index contains Timestamps (e.g. earnings_history).
    Returns [] on empty or error.
    """
    if df is None:
        return []
    try:
        import pandas as _pd
        if not isinstance(df, _pd.DataFrame) or df.empty:
            return []
        records = []
        for idx in df.index:
            if hasattr(idx, 'strftime'):
                idx_val = idx.strftime("%Y-%m-%d")
            else:
                idx_val = str(idx)
            record = {index_key: idx_val}
            for col in df.columns:
                record[str(col)] = serialize_value(df.loc[idx, col])
            records.append(record)
        return records
    except Exception:
        return []


def serialize_dataframe(df):
    """
    Convert a yfinance financial DataFrame (metrics as index, dates as columns)
    to {"periods": [...], "data": {metric: [values...]}} for easy table rendering.
    Returns None if df is None or empty.
    """
    if df is None:
        return None
    try:
        import pandas as _pd
        if not isinstance(df, _pd.DataFrame) or df.empty:
            return None

        periods = []
        for col in df.columns:
            if hasattr(col, 'strftime'):
                periods.append(col.strftime("%Y-%m-%d"))
            else:
                periods.append(str(col))

        data = {}
        for idx in df.index:
            row_key = str(idx)
            row_vals = []
            for col in df.columns:
                row_vals.append(serialize_value(df.loc[idx, col]))
            data[row_key] = row_vals

        return {"periods": periods, "data": data}
    except Exception:
        return None


def serialize_series_to_records(series):
    """
    Convert a pandas Series with a DatetimeIndex (e.g. t.dividends) to
    [{"date": "YYYY-MM-DD", "amount": float}, ...] sorted most-recent first.
    Returns [] on empty or error.
    """
    if series is None:
        return []
    try:
        import pandas as _pd
        import math as _math
        if not isinstance(series, _pd.Series) or series.empty:
            return []
        records = []
        for date, amount in series.items():
            try:
                if amount is None or (isinstance(amount, float) and _math.isnan(amount)):
                    continue
                date_str = date.strftime("%Y-%m-%d") if hasattr(date, 'strftime') else str(date)
                records.append({"date": date_str, "amount": round(float(amount), 6)})
            except Exception:
                continue
        return list(reversed(records))
    except Exception:
        return []


def safe_num(x):
    try:
        if x is None:
            return None
        if isinstance(x, (float, int)) and math.isnan(x):
            return None
        return float(x)
    except Exception:
        return None
