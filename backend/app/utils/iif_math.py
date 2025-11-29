import numpy as np
from typing import List, Dict, Any, Tuple

# IRT Scaling constant D. Set to 1.0 to match the default behavior of the mirt package
# when not explicitly specified (D=1 in mirt is standard).
D_SCALING_CONSTANT = 1.0

def _icc_3pl_non_guessing(a: float, b: float, theta: np.ndarray) -> np.ndarray:
    """
    Calculates the probability of a correct response (P*) for the 2PL part of the 3PL model.
    P*(theta) = 1 / (1 + exp(-D * a * (theta - b)))
    """
    # Ensure a, b are not None (fallback)
    a = a if a is not None else 1.0
    b = b if b is not None else 0.0
    
    exponent = D_SCALING_CONSTANT * a * (theta - b)
    return 1.0 / (1.0 + np.exp(-exponent))

def iif_3pl(a: float, b: float, c: float, theta: np.ndarray) -> np.ndarray:
    """
    Calculates the Item Information Function (IIF) for a single item
    using the 3-Parameter Logistic (3PL) model.

    The 3PL IIF formula is:
    I_i(theta) = a_i^2 * ( (1-c_i) / (c_i + P*(theta)) )^2 * P*(theta) * (1 - P*(theta))
    where P*(theta) is the probability from the 2PL part of the model.

    Args:
        a: Discrimination parameter.
        b: Difficulty parameter.
        c: Pseudo-guessing parameter.
        theta: Array of ability (theta) values.

    Returns:
        Array of information values at each theta point.
    """
    # Use the 2PL probability part
    P_star = _icc_3pl_non_guessing(a, b, theta)
    
    # Ensure c is not None and clamped between 0 and 1
    c = np.clip(c if c is not None else 0.0, 0.0, 1.0)
    
    # Calculate IIF components
    term1 = a**2
    term2 = ((1.0 - c) / (c + (1.0 - c) * P_star))**2 # Simplified, correct formula using P_star (ICC slope squared factor)
    term3 = P_star * (1.0 - P_star)
    
    # Final IIF is the product of the terms, multiplied by D_SCALING_CONSTANT^2 if D=1.7 was used.
    # Since D=1.0 is used, we omit D^2.
    # Note: If you switch D_SCALING_CONSTANT to 1.7, you must multiply the result by D_SCALING_CONSTANT**2
    return term1 * term2 * term3

def compute_item_information(
    item_params: List[Dict[str, Any]], 
    min_theta: float = -4.0, 
    max_theta: float = 4.0, 
    num_points: int = 101
) -> Dict[str, Dict[str, List[float]]]:
    """
    Calculates the IIF for all items across a specified range of ability (theta).

    Args:
        item_params: List of dictionaries, each containing 'item_id', 'discrimination', 
                     'difficulty', and 'guessing' parameters.
        min_theta: Minimum theta value.
        max_theta: Maximum theta value.
        num_points: Number of discrete theta points.

    Returns:
        A dictionary mapping item_id to a dictionary containing 
        'theta' and 'info' (IIF values), matching the structure 
        used internally by the frontend component state.
        
        Example: { "item_1": { "theta": [...], "info": [...] }, ... }
    """
    theta_grid = np.linspace(min_theta, max_theta, num_points)
    theta_list = theta_grid.round(6).tolist()
    
    all_iif_data: Dict[str, Dict[str, List[float]]] = {}
    
    for item in item_params:
        item_id = item.get("item_id")
        a = item.get("discrimination")
        b = item.get("difficulty")
        c = item.get("guessing")
        
        # Guard clause for missing critical parameters
        if not item_id or a is None or b is None:
            logger.warning(f"Skipping item {item_id} due to missing parameters (a:{a}, b:{b}).")
            continue

        # If c is missing (e.g., 2PL model), assume c=0 (or use the model's derived parameter if available)
        c = c if c is not None else 0.0
        
        # Calculate IIF
        iif_values = iif_3pl(a, b, c, theta_grid)
        
        all_iif_data[item_id] = {
            "theta": theta_list,
            "info": iif_values.round(8).tolist(),
        }
        
    return all_iif_data

if __name__ == '__main__':
    # Example usage for testing the math
    test_params = [
        {"item_id": "item_A", "discrimination": 1.5, "difficulty": 0.0, "guessing": 0.15},
        {"item_id": "item_B", "discrimination": 0.8, "difficulty": -1.0, "guessing": 0.0},
        {"item_id": "item_C", "discrimination": 2.0, "difficulty": 2.5, "guessing": 0.2},
    ]
    
    # Calculate IIF
    iif_results = compute_item_information(test_params)
    
    print("--- Python IIF Calculation Test ---")
    for item_id, data in iif_results.items():
        print(f"\nItem: {item_id}")
        print(f"  Theta points: {len(data['theta'])}")
        print(f"  Max Information: {max(data['info']):.6f}")
        # print(f"  First 5 Information points: {data['info'][:5]}")