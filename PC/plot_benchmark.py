#!/usr/bin/env python3

# plot_benchmark.py
# Usage: python3 plot_benchmark.py [data_file] [output_plot]

import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import sys
import os

def read_benchmark_data(filename):
    """Read benchmark data from file"""
    threads = []
    times = []
    
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if line.startswith('#') or not line:
                continue
            
            # Parse thread count and time
            parts = line.split()
            if len(parts) >= 2:
                try:
                    t = int(parts[0])
                    time_val = float(parts[1])
                    threads.append(t)
                    times.append(time_val)
                except ValueError:
                    continue
    
    return np.array(threads), np.array(times)

def fit_regression(threads, times):
    """
    Fit regression: t(n) = A + B / n
    For fitting, we use: t(n) * n = A * n + B
    
    Alternatively, we can transform: Let x = 1/n, then t = A + B*x
    """
    # Transform to 1/n for linear regression
    x = 1.0 / threads
    y = times
    
    # Perform linear regression (t = A + B * (1/n))
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    
    # slope corresponds to B, intercept corresponds to A
    A = intercept
    B = slope
    
    # Calculate R-squared
    r_squared = r_value ** 2
    
    # Generate predicted values
    x_smooth = np.linspace(min(x), max(x), 100)
    y_pred_smooth = A + B * x_smooth
    
    # Convert back to n space for plotting
    n_smooth = 1.0 / x_smooth
    t_pred_smooth = y_pred_smooth
    
    # Sort by n for plotting
    sort_idx = np.argsort(n_smooth)
    n_smooth = n_smooth[sort_idx]
    t_pred_smooth = t_pred_smooth[sort_idx]
    
    return A, B, r_squared, (n_smooth, t_pred_smooth)

def plot_results(threads, times, A, B, r_squared, prediction_curve, output_file):
    """Create the benchmark plot"""
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot 1: Time vs Threads
    ax1.scatter(threads, times, alpha=0.7, s=50, label='Measured data', color='blue')
    
    # Plot fitted curve
    n_pred, t_pred = prediction_curve
    ax1.plot(n_pred, t_pred, 'r-', linewidth=2, 
             label=f'Fit: t(n) = {A:.3f} + {B:.3f}/n\nR² = {r_squared:.4f}')
    
    ax1.set_xlabel('Number of Threads (n)', fontsize=12)
    ax1.set_ylabel('Time (seconds)', fontsize=12)
    ax1.set_title('Program Runtime vs Thread Count', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper right', fontsize=10)
    
    # Add horizontal line for asymptotic time A
    ax1.axhline(y=A, color='green', linestyle='--', alpha=0.7, 
                label=f'Asymptotic time: {A:.3f} s')
    ax1.legend(loc='upper right', fontsize=10)
    
    # Plot 2: 1/n transformation (linear fit)
    x_trans = 1.0 / threads
    x_smooth = np.linspace(min(x_trans), max(x_trans), 100)
    y_smooth = A + B * x_smooth
    
    ax2.scatter(x_trans, times, alpha=0.7, s=50, label='Transformed data', color='green')
    ax2.plot(x_smooth, y_smooth, 'r-', linewidth=2, 
             label=f'Fit: t = {A:.3f} + {B:.3f}·(1/n)')
    
    ax2.set_xlabel('1 / Number of Threads', fontsize=12)
    ax2.set_ylabel('Time (seconds)', fontsize=12)
    ax2.set_title('Linearized Fit (Transform)', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper left', fontsize=10)
    
    plt.tight_layout()
    
    # Save figure
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Plot saved to {output_file}")
    
    # Also show the plot if running interactively
    plt.show()

def main():
    # Parse command line arguments
    data_file = sys.argv[1] if len(sys.argv) > 1 else "benchmark_data.txt"
    output_plot = sys.argv[2] if len(sys.argv) > 2 else "benchmark_plot.png"
    
    # Check if data file exists
    if not os.path.exists(data_file):
        print(f"Error: Data file '{data_file}' not found!")
        print("Usage: python3 plot_benchmark.py [data_file] [output_plot]")
        print("Make sure to run run_benchmark.sh first to generate data.")
        sys.exit(1)
    
    # Read data
    print(f"Reading data from {data_file}...")
    threads, times = read_benchmark_data(data_file)
    
    if len(threads) == 0:
        print("Error: No valid data found in file!")
        sys.exit(1)
    
    print(f"Loaded {len(threads)} data points")
    print(f"Thread counts: {threads}")
    print(f"Times: {times}")
    
    # Fit regression
    print("\nFitting regression: t(n) = A + B / n")
    A, B, r_squared, prediction_curve = fit_regression(threads, times)
    
    # Print results
    print("\n=== Regression Results ===")
    print(f"Fitted model: t(n) = {A:.6f} + {B:.6f} / n")
    print(f"  where A = {A:.6f} seconds (asymptotic time)")
    print(f"  and B = {B:.6f} seconds⋅threads")
    print(f"R-squared: {r_squared:.6f}")
    print(f"Root Mean Square Error: {np.sqrt(np.mean((times - (A + B/threads))**2)):.6f}")
    
    # Calculate speedup
    if len(threads) > 1:
        serial_time = times[threads == 1][0] if 1 in threads else None
        if serial_time:
            print(f"\n=== Performance Metrics ===")
            print(f"Serial time (1 thread): {serial_time:.4f} s")
            for t in sorted(set(threads)):
                if t > 1:
                    time_t = times[threads == t][0]
                    speedup = serial_time / time_t
                    efficiency = speedup / t
                    print(f"Threads={t:2d}: time={time_t:.4f}s, speedup={speedup:.3f}x, efficiency={efficiency:.3f}")
    
    # Plot results
    print(f"\nGenerating plot...")
    plot_results(threads, times, A, B, r_squared, prediction_curve, output_plot)

if __name__ == "__main__":
    main()