import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm # type: ignore
from model import simulate

def calculate_stats(data):
    if not data: return {"mean": 0, "std": 0, "variance": 0}
    arr = np.array(data)
    return {
        "mean": np.mean(arr),
        "std": np.std(arr),
        "variance": np.var(arr)
    }

def confidence_interval(data, confidence=0.95):
    n = len(data)
    if n < 2: return (0, 0)
    mean = np.mean(data)
    std_err = np.std(data)/np.sqrt(n)
    z = 1.96
    return (mean - z*std_err, mean + z*std_err)

def run_experiments(param_name, values, config_base, n_runs=5):
    results = []
    for value in tqdm(values, desc=f"Testing {param_name}"):
        config = config_base.copy()
        config[param_name] = value
        run_stats = {
            "successful": [],
            "processing_means": [],
            "blocked": []
        }
        
        for _ in range(n_runs):
            res = simulate(config)
            stats = calculate_stats(res[5])
            run_stats["successful"].append(res[3])
            run_stats["processing_means"].append(stats["mean"])
            run_stats["blocked"].append(res[0] + res[2])
        
        results.append({
            "param_value": value,
            "successful_mean": np.mean(run_stats["successful"]),
            "successful_ci": confidence_interval(run_stats["successful"]),
            "time_mean": np.mean(run_stats["processing_means"]),
            "time_ci": confidence_interval(run_stats["processing_means"]),
            "blocked_mean": np.mean(run_stats["blocked"]),  
            "blocked_ci": confidence_interval(run_stats["blocked"])  
        })
    return results

from itertools import product
from concurrent.futures import ThreadPoolExecutor, as_completed

def run_simulation_multiple_times(config, n_runs):
    successful_attacks = [simulate(config)[3] for _ in range(n_runs)]
    return np.mean(successful_attacks), confidence_interval(successful_attacks)

def run_grid_search(base_config, param_grid, n_runs=3, max_workers=4):
    best_score = float('inf')
    best_params = {}
    history = []

    param_names = list(param_grid.keys())
    param_values = list(param_grid.values())
    all_combinations = [dict(zip(param_names, combo)) for combo in product(*param_values)]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(run_simulation_multiple_times, {**base_config, **combo}, n_runs): combo
                   for combo in all_combinations}
        
        for future in tqdm(as_completed(futures), total=len(futures), desc="Grid Search Progress"):
            mean_attacks, ci = future.result()
            current_params = futures[future]

            history.append({
                'params': current_params,
                'score': mean_attacks,
                'ci': ci
            })
            
            if mean_attacks < best_score:
                best_score = mean_attacks
                best_params = current_params

    return best_params, best_score, history

def plot_optimization_results(history):
    plt.figure(figsize=(12,6))
    x = [str(h['params']) for h in history]
    y = [h['score'] for h in history]
    ci = [h['ci'][1]-h['ci'][0] for h in history]
    
    plt.errorbar(x, y, yerr=ci, fmt='o', alpha=0.7, capsize=5)
    plt.title('Grid Search Optimization Results')
    plt.xlabel('Parameter Combinations')
    plt.ylabel('Successful Attacks (lower is better)')
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.grid(True)
    plt.show()

def plot_histogram(processing_times):
    plt.figure(figsize=(10,6))
    plt.hist(processing_times, bins=50, alpha=0.7)
    plt.title("Processing Time Distribution")
    plt.xlabel("Time (seconds)")
    plt.ylabel("Frequency")
    plt.show()

def plot_sensitivity(results, param_name, metric="successful"):
    values = [r["param_value"] for r in results]
    means = [r[f"{metric}_mean"] for r in results]
    cis = [r[f"{metric}_ci"] for r in results]
    
    plt.figure(figsize=(10,6))
    plt.errorbar(values, means, 
                 yerr=[(m - l) for (l, m) in cis], 
                 fmt='-o', capsize=5)
    plt.title(f"Sensitivity of {metric.capitalize()} Attacks to {param_name}")
    plt.xlabel(param_name)
    plt.ylabel("Number of Successful Attacks" if metric == "successful" else "Blocked Attacks")
    plt.grid(True)
    plt.show()