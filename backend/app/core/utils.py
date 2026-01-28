
import numpy as np
import math
from typing import Any

def sanitize_numpy(data: Any) -> Any:
    """
    Recursively converts numpy types to native Python types and handles non-finite floats.
    
    Converts:
    - numpy.integer -> int
    - numpy.floating -> float
    - numpy.ndarray -> list
    - NaN / Infinity -> None
    """
    if isinstance(data, dict):
        return {k: sanitize_numpy(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_numpy(v) for v in data]
    elif isinstance(data, (np.integer, np.int64, np.int32)):
        return int(data)
    elif isinstance(data, (np.floating, np.float64, np.float32)):
        val = float(data)
        if math.isnan(val) or math.isinf(val):
            return None
        return val
    elif isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return None
        return data
    elif isinstance(data, np.ndarray):
        return sanitize_numpy(data.tolist())
    elif isinstance(data, (np.bool_, bool)):
        return bool(data)
    else:
        return data
