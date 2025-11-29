import numpy as np

def get_theta_grid(n_points=41, theta_min=-4.0, theta_max=4.0):
    """
    Consistent theta grid for both ICC and TIF calculations
    """
    theta = np.linspace(theta_min, theta_max, n_points)
    return [float(round(t, 8)) for t in theta]

def generate_icc(a, b, c, item_id):
    """
    Generates the Item Characteristic Curve (ICC) points for a 3PL model.

    a: discrimination parameter
    b: difficulty parameter
    c: pseudo-guessing parameter
    item_id: identifier for the item
    """
    theta = get_theta_grid(41, -4, 4)
    theta_np = np.array(theta)  

    p = c + (1 - c) / (1 + np.exp(-a * (theta_np - b)))

    points = []
    for t, prob in zip(theta, p):
        points.append({
            "item_id": item_id,
            "theta": t,
            "probability": float(prob)
        })

    return points