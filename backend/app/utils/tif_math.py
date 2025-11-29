# tif_math.py
import numpy as np

def tif_3pl(items, n_points=41, theta_min=-4.0, theta_max=4.0, clamp=1e-9, round_info=8):
    """
    Use same parameters as ICC: 41 points from -4 to 4
    """
    try:
        # Same as ICC calculation
        theta = np.linspace(theta_min, theta_max, n_points)
        
        # Convert to clean Python floats (like ICC does)
        theta_clean = [float(round(t, 6)) for t in theta]  # Round to 6 decimal places
        theta_np = np.array(theta_clean)
        
        test_info = np.zeros_like(theta_np, dtype=float)

        for item in items:
            a = float(item.get("discrimination", 0.0))
            b = float(item.get("difficulty", 0.0))
            c = float(item.get("guessing", 0.0))

            z = a * (theta_np - b)
            L = 1.0 / (1.0 + np.exp(-z))

            p = c + (1.0 - c) * L
            p = np.clip(p, clamp, 1.0 - clamp)
            q = 1.0 - p

            dP = a * (1.0 - c) * L * (1.0 - L)
            info = (dP ** 2) / (p * q)

            test_info += info

        test_info_rounded = np.round(test_info, round_info)
        
        # Debug: Check types
        print(f"theta_clean type: {type(theta_clean)}, test_info type: {type(test_info_rounded)}")
        
        return theta_clean, test_info_rounded.tolist()

    except Exception as e:
        print(f"Error in tif_3pl: {e}")
        raise


def sem_from_tif(tif):
    """Standard Error of Measurement = 1 / sqrt(TIF)"""
    try:
        tif_array = np.array(tif, dtype=float)
        sem = 1 / np.sqrt(np.maximum(tif_array, 1e-9))
        return np.round(sem, 6).tolist()  # Round for clean display
    except Exception as e:
        print(f"Error in sem_from_tif: {e}")
        return [0] * len(tif) if isinstance(tif, list) else []