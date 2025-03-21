"""
Ray Actor Model Demo

This script demonstrates Ray's Actor model for stateful distributed computing:
1. Defining a Ray Actor class
2. Creating multiple Actor instances
3. Calling methods on Actors to maintain state
4. Processing tasks with state persistence

This pattern is useful for maintaining state across multiple calls
in distributed environments, such as maintaining a conversation history
in a CrewAI agent or tracking progress across workflow steps.
"""
import ray
import time
import random
import uuid
from datetime import datetime

print("Step 1: Initializing Ray cluster...")
# Initialize Ray
ray.init()
print(f"Ray initialized! Available resources: {ray.available_resources()}")

# Define a Ray Actor class
@ray.remote
class InsightProcessor:
    """
    Ray Actor for processing insights with persistent state.
    
    Actors maintain state between method calls, unlike regular
    remote functions which are stateless.
    """
    
    def __init__(self, processor_id, specialty="general"):
        """Initialize the actor with an ID and specialty."""
        self.processor_id = processor_id
        self.specialty = specialty
        self.processed_count = 0
        self.insights_history = []
        self.start_time = datetime.now()
        print(f"Actor {processor_id} initialized with specialty: {specialty}")
    
    def process_insight(self, insight, metadata=None):
        """
        Process an insight and maintain state about what was processed.
        
        Args:
            insight: The text insight to process
            metadata: Optional metadata about the insight
            
        Returns:
            Processed result with actor's state information
        """
        # Simulate processing time based on complexity
        complexity = len(insight) / 10
        time.sleep(random.uniform(0.2, 0.5) * complexity / 10)
        
        # Update actor state
        self.processed_count += 1
        self.insights_history.append(insight)
        
        # Generate priority based on specialty and insight
        if self.specialty in insight.lower():
            priority = random.randint(7, 10)  # Higher priority for specialized insights
        else:
            priority = random.randint(1, 6)
        
        # Create and return result
        result = {
            "insight": insight,
            "priority": priority,
            "processed_by": f"Actor-{self.processor_id}",
            "processed_count": self.processed_count,
            "processing_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "actor_uptime": str(datetime.now() - self.start_time).split('.')[0],
            "specialty_match": self.specialty in insight.lower(),
        }
        
        if metadata:
            result["metadata"] = metadata
            
        return result
    
    def get_stats(self):
        """Return statistics about this actor's processing history."""
        return {
            "processor_id": self.processor_id,
            "specialty": self.specialty,
            "processed_count": self.processed_count,
            "uptime": str(datetime.now() - self.start_time).split('.')[0],
            "insight_history_size": len(self.insights_history),
        }


def main():
    """Main function to demonstrate Ray's Actor model."""
    # Sample insights with different focus areas
    insights = [
        "Sales have increased by 15% in Q2",
        "Customer retention rate has improved by 8%",
        "Mobile users account for 60% of traffic",
        "Sales of premium products are up 22%",
        "Customer satisfaction score is at 4.2/5",
        "Mobile app downloads increased by 30%",
        "Sales forecast indicates 18% growth next quarter",
        "Customer support ticket resolution time improved by 15%",
        "Mobile payment adoption is up 25% from last month",
    ]
    
    # Create specialized actors for different types of insights
    print("\nStep 2: Creating specialized actor instances...")
    sales_actor = InsightProcessor.remote(processor_id="sales-1", specialty="sales")
    customer_actor = InsightProcessor.remote(processor_id="customer-1", specialty="customer")
    mobile_actor = InsightProcessor.remote(processor_id="mobile-1", specialty="mobile")
    
    # Route insights to the appropriate specialized actor
    print("\nStep 3: Routing insights to specialized actors...")
    refs = []
    
    for insight in insights:
        # Route the insight to the most appropriate actor
        if "sales" in insight.lower():
            actor = sales_actor
            print(f"Routing to sales actor: '{insight}'")
        elif "customer" in insight.lower():
            actor = customer_actor
            print(f"Routing to customer actor: '{insight}'")
        elif "mobile" in insight.lower():
            actor = mobile_actor
            print(f"Routing to mobile actor: '{insight}'")
        else:
            # Round-robin for general insights
            actors = [sales_actor, customer_actor, mobile_actor]
            actor = actors[random.randint(0, 2)]
            print(f"Routing to random actor: '{insight}'")
        
        # Submit the task to the selected actor
        refs.append(actor.process_insight.remote(insight, {"timestamp": time.time()}))
    
    # Get all results
    print("\nStep 4: Waiting for all processing to complete...")
    results = ray.get(refs)
    
    # Print results
    print("\nStep 5: Processed Insights:")
    for i, result in enumerate(results, 1):
        priority_label = "HIGH" if result['priority'] >= 7 else "MEDIUM" if result['priority'] >= 4 else "LOW"
        print(f"{i}. '{result['insight']}' (Priority: {result['priority']} - {priority_label})")
        print(f"   Processed by: {result['processed_by']}")
        print(f"   Specialty match: {result['specialty_match']}")
        print(f"   Actor insight count: {result['processed_count']}")
        print()
    
    # Get actor statistics to show state persistence
    print("\nStep 6: Actor Statistics (showing state persistence):")
    actor_stats = ray.get([
        sales_actor.get_stats.remote(),
        customer_actor.get_stats.remote(),
        mobile_actor.get_stats.remote()
    ])
    
    for stats in actor_stats:
        print(f"Actor {stats['processor_id']} (specialty: {stats['specialty']}):")
        print(f"  Processed {stats['processed_count']} insights")
        print(f"  Uptime: {stats['uptime']}")
        print()
    
    # Shutdown Ray
    print("Step 7: Shutting down Ray...")
    ray.shutdown()
    print("Ray shutdown complete.")
    print("\nThis demonstrates how Ray Actors can maintain state across multiple calls in Kodosumi workflows.")

if __name__ == "__main__":
    main() 