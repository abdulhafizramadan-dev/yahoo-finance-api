import math


def serialize_value(v):
    try:
        if v is None:
            return None
        if isinstance(v, (str, bool, int, float)):
            return v
        try:
            import pandas as _pd
            import numpy as _np

            if isinstance(v, _pd.Timestamp):
                return v.isoformat()
            if isinstance(v, (_np.integer,)):
                return int(v)
            if isinstance(v, (_np.floating,)):
                return float(v)
        except Exception:
            pass
        return str(v)
    except Exception:
        return str(v)


def safe_num(x):
    try:
        if x is None:
            return None
        if isinstance(x, (float, int)) and math.isnan(x):
            return None
        return float(x)
    except Exception:
        return None

