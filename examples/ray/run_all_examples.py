#!/usr/bin/env python
"""
Ray Examples Runner

This script runs all Ray examples in sequence, demonstrating the progression
from basic Ray concepts to more advanced patterns.

Usage:
    python run_all_examples.py  # Run all examples
    python run_all_examples.py basic  # Run only the basic example
    python run_all_examples.py parallel  # Run only the parallel example
    python run_all_examples.py actor  # Run only the actor example
"""
import os
import sys
import time
import subprocess
import ray

def print_header(title, width=80):
    """Print a formatted header."""
    print("\n" + "=" * width)
    print(f"{title}".center(width))
    print("=" * width + "\n")

def run_example(script_name, description):
    """Run a single Ray example script."""
    print_header(f"Running {script_name}: {description}")
    
    # Make sure Ray is shutdown before running each example
    if ray.is_initialized():
        print("Shutting down existing Ray instance...")
        ray.shutdown()
        time.sleep(1)
    
    # Run the example script as a subprocess
    try:
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name)
        result = subprocess.run(["python", script_path], check=True)
        print(f"\nExample {script_name} completed with exit code {result.returncode}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nError running example {script_name}: {e}")
        return False

def main():
    """Run Ray examples based on command line arguments."""
    examples = [
        ("ray_test.py", "Basic Ray Remote Functions"),
        ("ray_parallel_test.py", "Ray Parallel Processing"),
        ("ray_actor_model.py", "Ray Actor Model for Stateful Processing")
    ]
    
    # Filter examples based on command line args
    if len(sys.argv) > 1:
        filter_term = sys.argv[1].lower()
        if filter_term == "basic":
            examples = [examples[0]]
        elif filter_term == "parallel":
            examples = [examples[1]]
        elif filter_term == "actor":
            examples = [examples[2]]
        else:
            print(f"Unknown example filter: {filter_term}")
            print("Available filters: basic, parallel, actor")
            return
    
    print_header("RAY EXAMPLES RUNNER")
    print(f"Running {len(examples)} Ray examples to demonstrate distributed computing patterns")
    print(f"Examining current Ray status...")
    
    # Check if Ray is already running
    try:
        subprocess.run(["ray", "status"], check=True, capture_output=True)
        print("Ray is already running! Using existing cluster.")
    except subprocess.CalledProcessError:
        print("Ray is not running. Starting Ray...")
        try:
            subprocess.run(["ray", "start", "--head"], check=True)
            print("Ray started successfully!")
        except subprocess.CalledProcessError as e:
            print(f"Error starting Ray: {e}")
            return
    
    # Run all selected examples
    results = []
    for script_name, description in examples:
        success = run_example(script_name, description)
        results.append((script_name, success))
    
    # Print summary
    print_header("SUMMARY")
    for script_name, success in results:
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"{status}: {script_name}")
    
    # Don't shut down Ray since it might have been running before we started
    print("\nRay examples completed. Ray cluster is still running.")
    print("If you want to stop Ray, run 'ray stop'")

if __name__ == "__main__":
    main() 