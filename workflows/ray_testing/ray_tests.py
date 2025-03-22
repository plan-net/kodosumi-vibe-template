#!/usr/bin/env python

"""
Ray test functions adapted from examples with added markdown integration.
These test different Ray features and patterns.
"""

import os
import ray
import time
import random
import uuid
import platform
from typing import List, Dict, Any
from kodosumi.tracer import markdown


# =============== BASIC TEST ===============
def basic_test() -> str:
    """
    Basic Ray test with simple remote functions.
    
    Returns:
        Markdown formatted results
    """
    markdown("**Basic Ray Test: Initializing...**")
    
    start_time = time.time()
    results = []
    
    # Define a simple remote function
    @ray.remote
    def say_hello(name):
        """Simple remote function that returns a greeting."""
        hostname = platform.node()
        pid = os.getpid()
        return f"Hello {name}, from process {pid} on {hostname}"
    
    @ray.remote
    def square(x):
        """Square a number remotely."""
        return x * x
    
    # Execute remote functions in parallel
    markdown("**Executing remote functions...**")
    names = ["Alice", "Bob", "Charlie", "Dave", "Eve"]
    
    # Use Ray to execute tasks in parallel
    name_refs = [say_hello.remote(name) for name in names]
    
    # Get results as they complete
    for i, ref in enumerate(name_refs):
        result = ray.get(ref)
        markdown(f"**Result {i+1}:** {result}")
        results.append(result)
    
    # Compare with serial execution
    markdown("**Testing computation performance...**")
    
    # Serial execution time for comparison
    serial_start = time.time()
    serial_result = [i * i for i in range(1000000)]
    serial_time = time.time() - serial_start
    markdown(f"**Serial computation time:** {serial_time:.6f} seconds")
    
    # Parallel execution with Ray
    parallel_start = time.time()
    square_refs = [square.remote(i) for i in range(1000000)]
    parallel_result = ray.get(square_refs)
    parallel_time = time.time() - parallel_start
    markdown(f"**Parallel computation time:** {parallel_time:.6f} seconds")
    
    # Calculate speedup
    if serial_time > 0:
        speedup = serial_time / parallel_time
        markdown(f"**Speedup factor:** {speedup:.2f}x")
    else:
        markdown("**Speedup factor:** N/A (serial time too small)")
    
    # Compile results
    total_time = time.time() - start_time
    markdown(f"**Basic Ray test completed in {total_time:.2f} seconds**")
    
    # Format markdown result
    output = f"""
# Ray Basic Test Results

## Environment
- **Host:** {platform.node()}
- **Ray Version:** {ray.__version__}
- **Platform:** {platform.platform()}

## Greeting Test
Successfully executed {len(names)} remote greetings:

{"".join([f"- {r}\n" for r in results])}

## Performance Test
- **Serial computation time:** {serial_time:.6f} seconds
- **Parallel computation time:** {parallel_time:.6f} seconds
- **Speedup factor:** {speedup:.2f}x

## Summary
Test completed in {total_time:.2f} seconds.
"""
    return output


# =============== PARALLEL TEST ===============
def parallel_test() -> str:
    """
    Ray test demonstrating parallel data processing.
    
    Returns:
        Markdown formatted results
    """
    markdown("**Parallel Ray Test: Initializing...**")
    
    # Generate sample data
    markdown("**Generating sample data...**")
    sample_size = 100
    sample_data = [
        {"id": i, "value": random.randint(1, 1000)} 
        for i in range(sample_size)
    ]
    
    # Define processing function
    @ray.remote
    def process_item(item):
        """Process a single data item."""
        # Simulate processing time
        time.sleep(0.05)
        
        worker_id = f"worker-{uuid.uuid4().hex[:8]}"
        timestamp = time.strftime("%H:%M:%S")
        
        # Process the item
        result = {
            "id": item["id"],
            "original_value": item["value"],
            "processed_value": item["value"] * 2,  # Simple transformation
            "worker_id": worker_id,
            "timestamp": timestamp
        }
        
        return result
    
    # Execute parallel processing
    markdown("**Processing data in parallel...**")
    start_time = time.time()
    
    # Submit all tasks in parallel
    refs = [process_item.remote(item) for item in sample_data]
    
    # Track progress
    pending_refs = list(refs)
    processed_results = []
    
    # Process results as they complete
    while pending_refs:
        # Use ray.wait to get completed tasks
        finished_refs, pending_refs = ray.wait(pending_refs, num_returns=min(10, len(pending_refs)))
        
        # Get the results from finished tasks
        for ref in finished_refs:
            result = ray.get(ref)
            processed_results.append(result)
        
        # Update progress
        progress = (len(processed_results) / sample_size) * 100
        markdown(f"**Progress: {progress:.1f}% ({len(processed_results)}/{sample_size})**")
    
    # Calculate statistics
    parallel_time = time.time() - start_time
    
    # Execute sequential processing for comparison
    markdown("**Processing data sequentially for comparison...**")
    sequential_start = time.time()
    
    sequential_results = []
    for item in sample_data:
        # Simulate processing time
        time.sleep(0.05)
        
        # Process the item
        result = {
            "id": item["id"],
            "original_value": item["value"],
            "processed_value": item["value"] * 2,
            "worker_id": "sequential",
            "timestamp": time.strftime("%H:%M:%S")
        }
        
        sequential_results.append(result)
    
    sequential_time = time.time() - sequential_start
    
    # Display results
    markdown(f"**Parallel processing completed in {parallel_time:.2f} seconds**")
    markdown(f"**Sequential processing completed in {sequential_time:.2f} seconds**")
    
    # Calculate speedup
    speedup = sequential_time / parallel_time if parallel_time > 0 else "N/A"
    markdown(f"**Speedup: {speedup:.2f}x**")
    
    # Identify workers
    workers = set([r["worker_id"] for r in processed_results])
    markdown(f"**Number of workers used: {len(workers)}**")
    
    # Format markdown result
    output = f"""
# Ray Parallel Processing Test Results

## Configuration
- **Sample Size:** {sample_size} items
- **Ray Version:** {ray.__version__}
- **Workers Used:** {len(workers)}

## Performance Comparison
- **Parallel processing time:** {parallel_time:.2f} seconds
- **Sequential processing time:** {sequential_time:.2f} seconds
- **Speedup factor:** {speedup:.2f}x

## Worker Distribution
{", ".join(sorted(workers))}

## Sample Results
First 5 processed items:
```
{processed_results[:5]}
```

## Summary
Successfully processed {len(processed_results)} items using Ray's parallel processing capabilities.
"""
    return output


# =============== ACTOR MODEL TEST ===============
def actor_model_test() -> str:
    """
    Ray test demonstrating the actor model for stateful processing.
    
    Returns:
        Markdown formatted results
    """
    markdown("**Actor Model Test: Initializing...**")
    
    # Create test data
    transaction_types = ["deposit", "withdrawal", "transfer", "payment", "refund"]
    accounts = [f"account_{i}" for i in range(1, 6)]
    
    # Generate 50 random transactions
    transactions = []
    for i in range(50):
        transaction = {
            "id": i,
            "account": random.choice(accounts),
            "type": random.choice(transaction_types),
            "amount": round(random.uniform(10, 1000), 2)
        }
        transactions.append(transaction)
    
    # Define an actor to maintain account state
    @ray.remote
    class AccountManager:
        """Ray Actor that maintains state for multiple accounts."""
        
        def __init__(self):
            """Initialize the account manager with empty accounts."""
            self.accounts = {account: 0.0 for account in accounts}
            self.transaction_counts = {account: 0 for account in accounts}
            self.transaction_history = {account: [] for account in accounts}
        
        def process_transaction(self, transaction):
            """Process a single transaction and update account state."""
            account = transaction["account"]
            amount = transaction["amount"]
            tx_type = transaction["type"]
            
            # Update account balance based on transaction type
            if tx_type == "deposit":
                self.accounts[account] += amount
            elif tx_type == "withdrawal":
                self.accounts[account] -= amount
            elif tx_type == "transfer":
                # Simplified transfer (just reduces the balance)
                self.accounts[account] -= amount
            elif tx_type == "payment":
                self.accounts[account] -= amount
            elif tx_type == "refund":
                self.accounts[account] += amount
            
            # Update transaction count
            self.transaction_counts[account] += 1
            
            # Add to history
            self.transaction_history[account].append({
                "id": transaction["id"],
                "type": tx_type,
                "amount": amount,
                "balance_after": self.accounts[account]
            })
            
            return {
                "account": account,
                "transaction_id": transaction["id"],
                "new_balance": self.accounts[account],
                "transaction_count": self.transaction_counts[account]
            }
        
        def get_account_state(self, account=None):
            """Get the current state of all accounts or a specific account."""
            if account:
                return {
                    "balance": self.accounts.get(account, 0),
                    "transaction_count": self.transaction_counts.get(account, 0),
                    "history": self.transaction_history.get(account, [])
                }
            else:
                return {
                    "accounts": self.accounts,
                    "transaction_counts": self.transaction_counts
                }
    
    # Begin actor test
    markdown("**Creating AccountManager actor...**")
    manager = AccountManager.remote()
    
    # Process transactions
    markdown("**Processing transactions...**")
    results = []
    
    start_time = time.time()
    for i, transaction in enumerate(transactions):
        result = ray.get(manager.process_transaction.remote(transaction))
        results.append(result)
        
        # Show progress
        if (i + 1) % 10 == 0:
            markdown(f"**Processed {i + 1}/{len(transactions)} transactions**")
    
    # Get final account states
    markdown("**Retrieving final account states...**")
    account_states = ray.get(manager.get_account_state.remote())
    
    # Get individual account details
    account_details = {}
    for account in accounts:
        account_details[account] = ray.get(manager.get_account_state.remote(account))
    
    processing_time = time.time() - start_time
    markdown(f"**Actor model test completed in {processing_time:.2f} seconds**")
    
    # Format markdown result
    output = f"""
# Ray Actor Model Test Results

## Configuration
- **Transactions:** {len(transactions)}
- **Accounts:** {len(accounts)}
- **Ray Version:** {ray.__version__}

## Final Account Balances
|Account|Balance|Transactions|
|-------|------:|----------:|
"""
    
    # Add account details
    for account in sorted(accounts):
        output += f"|{account}|${account_states['accounts'][account]:.2f}|{account_states['transaction_counts'][account]}|\n"
    
    # Add transaction distribution
    output += """
## Transaction Type Distribution
|Type|Count|
|----|----:|
"""
    
    # Count transaction types
    tx_type_counts = {}
    for tx in transactions:
        tx_type = tx["type"]
        if tx_type not in tx_type_counts:
            tx_type_counts[tx_type] = 0
        tx_type_counts[tx_type] += 1
    
    for tx_type, count in sorted(tx_type_counts.items()):
        output += f"|{tx_type}|{count}|\n"
    
    # Add sample transaction history for one account
    sample_account = accounts[0]
    sample_history = account_details[sample_account]["history"][:5]  # First 5 transactions
    
    output += f"""
## Sample Transaction History for {sample_account}
|ID|Type|Amount|Balance After|
|--|----|-----:|------------:|
"""
    
    for tx in sample_history:
        output += f"|{tx['id']}|{tx['type']}|${tx['amount']:.2f}|${tx['balance_after']:.2f}|\n"
    
    output += f"""
## Summary
- **Processing Time:** {processing_time:.2f} seconds
- **Transactions Processed:** {len(transactions)}
- **State Maintained:** Yes (balances, counts, history)

Actor pattern successfully maintained state across {len(transactions)} method calls.
"""
    
    return output 