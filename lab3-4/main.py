import json
import time
import os
import numpy as np
from analysis import run_experiments, plot_histogram, plot_sensitivity, calculate_stats, confidence_interval, run_grid_search, plot_optimization_results
from model import simulate

def load_config(file_path="config.json"):
    with open(file_path) as f:
        config = json.load(f)
        
    required_params = [
        "lambda_attacks", "ids_mu", "ids_sigma",
        "ips_mu", "ips_sigma", "ips_block_rate",
        "correct_detection"
    ]
        
    for param in required_params:
        if param not in config:
            raise ValueError(f"Параметр отсутствует: {param}")
                
    return config

def main():
    config = load_config()
    
    start = time.time()
    results = simulate(config)
    end = time.time()
    
    print("Результаты моделирования:")
    print(f"Заблокировано Firewall: {results[0]:,}")
    print(f"Обнаружено IDS: {results[1]:,}")
    print(f"Заблокировано IPS: {results[2]:,}")
    print(f"Успешные атаки: {results[3]:,}")
    print(f"Общее время обработки: {results[4]/3600:.2f} часов")
    print(f"Время выполнения моделирования: {end-start:.2f} секунд\n")
    
    stats = calculate_stats(results[5])
    print("Статистические характеристики времени обработки:")
    print(f"Среднее значение: {stats['mean']:.4f}")
    print(f"Дисперсия: {stats['variance']:.4f}")
    print(f"Стандартное отклонение: {stats['std']:.4f}")
    
    ci = confidence_interval(results[5])
    print(f"Доверительный интервал (95%): ({ci[0]:.4f}, {ci[1]:.4f})\n")
    
    plot_histogram(results[5])
    
    print("\nRunning sensitivity analysis...")
    br_results = run_experiments(
        "ips_block_rate", 
        np.arange(0.7, 0.96, 0.05),
        config
    )
    
    cd_results = run_experiments(
        "correct_detection",
        np.arange(0.8, 1.0, 0.03),
        config
    )
    
    plot_sensitivity(br_results, "IPS Block Rate")
    plot_sensitivity(cd_results, "Detection Accuracy")
    plot_sensitivity(br_results, "IPS Block Rate", metric="blocked")

    print("\nRunning parameter optimization...")
    param_grid = {
        'ips_block_rate': np.arange(0.7, 0.96, 0.05),
        'correct_detection': np.arange(0.85, 0.99, 0.03),
        'ids_mu': np.arange(3, 6, 0.5)
    }
    
    start_time = time.time()
    best_params, best_score, history = run_grid_search(
        base_config=config,
        param_grid=param_grid,
        n_runs=3
    )
    end_time = time.time()
    
    print("\nOptimization Results:")
    print(f"Best parameters: {best_params}")
    print(f"Minimum successful attacks: {best_score:.1f}")
    print(f"Optimization time: {end_time-start_time:.2f} seconds")
    
    plot_optimization_results(history)
    
    print("\nRunning simulation with optimized parameters...")
    optimized_config = config.copy()
    optimized_config.update(best_params)
    
    optimized_results = simulate(optimized_config)

if __name__ == "__main__":
    main()