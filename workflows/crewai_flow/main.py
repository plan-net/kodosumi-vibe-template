#!/usr/bin/env python

import json
import os
import asyncio
import ray
import sys
import time
import random
from typing import List, Dict, Any

from dotenv import load_dotenv
from pydantic import BaseModel

from crewai.flow import Flow, listen, start

# Import your crew classes here
from workflows.crewai_flow.crews.first_crew.first_crew import FirstCrew, FirstCrewOutput

# Load environment variables from .env file
load_dotenv()

# Check if we're running in Kodosumi environment
# Kodosumi will handle Ray initialization for us
is_kodosumi = os.environ.get("KODOSUMI_ENVIRONMENT") == "true"

# Sample datasets for demonstration
SAMPLE_DATASETS = {
    "sales_data": {
        "name": "Quarterly Sales Data",
        "description": "Sales data for the last 4 quarters across different regions and product categories.",
        "sample": [
            {"quarter": "Q1", "region": "North", "category": "Electronics", "sales": 125000},
            {"quarter": "Q1", "region": "South", "category": "Electronics", "sales": 87000},
            {"quarter": "Q1", "region": "East", "category": "Furniture", "sales": 118000},
            {"quarter": "Q1", "region": "West", "category": "Clothing", "sales": 92000},
            {"quarter": "Q2", "region": "North", "category": "Electronics", "sales": 132000},
            {"quarter": "Q2", "region": "South", "category": "Furniture", "sales": 97000},
            {"quarter": "Q3", "region": "East", "category": "Clothing", "sales": 105000},
            {"quarter": "Q4", "region": "West", "category": "Electronics", "sales": 145000}
        ]
    },
    "customer_feedback": {
        "name": "Customer Feedback Survey",
        "description": "Results from a recent customer satisfaction survey with ratings and comments.",
        "sample": [
            {"customer_id": 1001, "rating": 4.5, "comment": "Great product, fast delivery!"},
            {"customer_id": 1002, "rating": 3.0, "comment": "Product was okay, but shipping took too long."},
            {"customer_id": 1003, "rating": 5.0, "comment": "Excellent customer service and quality."},
            {"customer_id": 1004, "rating": 2.5, "comment": "The product didn't meet my expectations."},
            {"customer_id": 1005, "rating": 4.0, "comment": "Good value for money, would recommend."}
        ]
    }
}

class CrewAIFlowState(BaseModel):
    """
    Define your flow state here.
    This will hold all the data that is passed between steps in the flow.
    """
    dataset_name: str = "customer_feedback"  # Default dataset
    output_format: str = "markdown"   # Default output format (markdown or json)
    analysis_results: Dict[str, Any] = {}
    parallel_processing_results: List[Dict[str, Any]] = []
    final_insights: Dict[str, Any] = {}

class CrewAIFlow(Flow[CrewAIFlowState]):
    """
    Define your flow steps here.
    Each step is a method decorated with @listen that takes the output of a previous step.
    """

    @start()
    def validate_inputs(self):
        """
        Validate the inputs to the flow.
        This is the first step in the flow.
        """
        print("Validating inputs...")
        
        # Check if the dataset exists
        if self.state.dataset_name not in SAMPLE_DATASETS:
            print(f"Dataset '{self.state.dataset_name}' not found. Using default dataset.")
            self.state.dataset_name = "customer_feedback"
        
        print(f"Using dataset: {self.state.dataset_name}")

    @listen(validate_inputs)
    def analyze_data(self):
        """
        First step in the flow.
        This step uses a CrewAI crew to analyze the dataset.
        """
        print("Analyzing data...")
        
        # Get the selected dataset
        dataset = SAMPLE_DATASETS[self.state.dataset_name]
        
        try:
            # Check if OpenAI API key is set and valid
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set")
            
            # Check if the API key is a placeholder
            if api_key.startswith("your_") or api_key.startswith("sk-your_"):
                raise ValueError("OPENAI_API_KEY is a placeholder value. Please set a valid API key.")
            
            print(f"Using CrewAI to analyze {dataset['name']}...")
            
            # Create the crew
            crew_instance = FirstCrew()
            crew = crew_instance.crew()
            
            # Prepare the task inputs
            task_inputs = {
                "dataset_name": dataset["name"],
                "dataset_description": dataset["description"],
                "sample_data": json.dumps(dataset["sample"], indent=2)
            }
            
            # Run the crew
            crew_result = crew.kickoff(inputs=task_inputs)
            
            # Parse the crew output
            # The CrewOutput object structure is different than expected
            try:
                # Print the crew_result to debug
                print(f"CrewOutput type: {type(crew_result)}")
                print(f"CrewOutput dir: {dir(crew_result)}")
                
                # Try to access the result directly
                if hasattr(crew_result, 'result'):
                    # If there's a result attribute, use it
                    result_text = str(crew_result.result)
                elif hasattr(crew_result, 'raw'):
                    # If there's a raw attribute, use it
                    result_text = str(crew_result.raw)
                else:
                    # Otherwise, convert the entire object to a string
                    result_text = str(crew_result)
                
                print(f"Using result text: {result_text[:100]}...")
                
                # Parse the result text to extract summary, insights, and recommendations
                # This is a simplified parsing approach - in a real application, you might want to use a more robust parsing method
                lines = result_text.split('\n')
                summary = ""
                insights = []
                recommendations = []
                
                current_section = None
                for line in lines:
                    line = line.strip()
                    if "Summary" in line or "summary" in line:
                        current_section = "summary"
                        continue
                    elif "Key Business Insights" in line or "Insights" in line or "insights" in line:
                        current_section = "insights"
                        continue
                    elif "Actionable Recommendations" in line or "Recommendations" in line or "recommendations" in line:
                        current_section = "recommendations"
                        continue
                    
                    if current_section == "summary" and line:
                        summary += line + " "
                    elif current_section == "insights" and line and (line[0].isdigit() or line.startswith('-')):
                        # Extract the insight text after the number or dash
                        if line[0].isdigit() and '.' in line:
                            insights.append(line[line.find(".")+1:].strip())
                        elif line.startswith('-'):
                            insights.append(line[1:].strip())
                        else:
                            insights.append(line.strip())
                    elif current_section == "recommendations" and line and (line[0].isdigit() or line.startswith('-')):
                        # Extract the recommendation text after the number or dash
                        if line[0].isdigit() and '.' in line:
                            recommendations.append(line[line.find(".")+1:].strip())
                        elif line.startswith('-'):
                            recommendations.append(line[1:].strip())
                        else:
                            recommendations.append(line.strip())
                
                # If we couldn't parse the output properly, use default values
                if not summary:
                    summary = f"Analysis of {dataset['name']} dataset"
                
                if not insights:
                    insights = ["No specific insights could be extracted from the analysis"]
                
                if not recommendations:
                    recommendations = ["No specific recommendations could be extracted from the analysis"]
                
                self.state.analysis_results = {
                    "summary": summary.strip(),
                    "insights": insights,
                    "recommendations": recommendations
                }
            except Exception as parsing_error:
                print(f"Error parsing crew output: {parsing_error}")
                # Fall through to the fallback response
                raise
            
            print("CrewAI analysis completed successfully.")
            
        except Exception as e:
            # Fallback to simulated response if CrewAI fails
            print(f"CrewAI analysis failed: {e}")
            print(f"Using simulated response for {dataset['name']} dataset...")
            
            # Simulated analysis results based on the dataset
            if self.state.dataset_name == "sales_data":
                self.state.analysis_results = {
                    "summary": f"Analysis of {dataset['name']} reveals distinct regional preferences for product categories, with Electronics showing the strongest overall performance, particularly in Q4.",
                    "insights": [
                        "Electronics is the highest-performing category, with peak sales in Q4 in the West region.",
                        "Regional specialization exists across different product categories.",
                        "Seasonal trends are evident, with Q4 showing the highest sales for Electronics.",
                        "The North region demonstrates consistent performance across quarters.",
                        "There's potential for growth in underperforming category-region combinations."
                    ],
                    "recommendations": [
                        "Increase Electronics inventory in all regions for Q4 to capitalize on seasonal demand.",
                        "Develop targeted marketing campaigns for Electronics in the West region.",
                        "Investigate why South region has lower Electronics sales.",
                        "Consider expanding Furniture offerings in the East and South regions.",
                        "Implement cross-selling strategies in regions with single-category strength."
                    ]
                }
            elif self.state.dataset_name == "customer_feedback":
                self.state.analysis_results = {
                    "summary": f"Analysis of {dataset['name']} indicates overall positive customer satisfaction with an average rating of 3.8 out of 5.",
                    "insights": [
                        "High ratings correlate with mentions of customer service and product quality.",
                        "Mid-range ratings often mention good value but concerns about delivery times.",
                        "Lower ratings frequently mention unmet expectations about the product.",
                        "Shipping and delivery time is a recurring theme across all rating levels.",
                        "Customers who mention 'value for money' tend to be satisfied overall."
                    ],
                    "recommendations": [
                        "Enhance the shipping process to address the most common concern.",
                        "Leverage positive customer service experiences in marketing materials.",
                        "Improve product descriptions to better set customer expectations.",
                        "Implement a follow-up system for customers who rate products below 3.0.",
                        "Create a loyalty program for highly satisfied customers."
                    ]
                }
        
        print("Data analysis completed.")

    @listen(analyze_data)
    def process_insights_in_parallel(self):
        """
        Second step in the flow.
        This step demonstrates how to parallelize processing of multiple items using Ray.
        """
        print("Processing insights in parallel...")
        
        # Extract insights from the analysis results
        insights = self.state.analysis_results.get("insights", [])
        
        if not insights:
            print("No insights to process.")
            return
        
        # Process insights using Ray
        try:
            # Define a remote function to process each insight
            @ray.remote
            def process_insight(insight, index):
                """Process a single insight using Ray."""
                # Simulate some processing time
                time.sleep(random.uniform(0.5, 1.0))
                
                # Generate a priority score based on the insight
                priority = random.randint(1, 10)
                
                return {
                    "insight": insight,
                    "priority": priority,
                    "processed_by": f"Worker-{index}"
                }
            
            # Process all insights in parallel
            print("Using Ray for parallel processing...")
            process_tasks = [process_insight.remote(insight, i) for i, insight in enumerate(insights)]
            processed_results = ray.get(process_tasks)
            
        except Exception as e:
            # Fallback to local processing if Ray fails
            print(f"Ray processing failed: {e}. Falling back to local processing...")
            processed_results = []
            for i, insight in enumerate(insights):
                # Simulate some processing time
                time.sleep(random.uniform(0.1, 0.3))
                
                # Generate a priority score
                priority = random.randint(1, 10)
                
                processed_results.append({
                    "insight": insight,
                    "priority": priority,
                    "processed_by": f"Local-{i}"
                })
        
        # Sort results by priority (highest first)
        self.state.parallel_processing_results = sorted(
            processed_results, 
            key=lambda x: x["priority"], 
            reverse=True
        )
        
        print(f"Processed {len(processed_results)} insights in parallel.")

    @listen(process_insights_in_parallel)
    def finalize_results(self):
        """
        Final step in the flow.
        This step aggregates the results from previous steps.
        """
        print("Finalizing results...")
        
        # Combine the original analysis with the prioritized insights
        self.state.final_insights = {
            "summary": self.state.analysis_results.get("summary", "No summary available"),
            "prioritized_insights": self.state.parallel_processing_results,
            "recommendations": self.state.analysis_results.get("recommendations", []),
            "dataset_analyzed": self.state.dataset_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        print("Flow completed successfully!")
        
        # Print a summary of the results
        print("\n=== ANALYSIS RESULTS ===")
        print(f"Dataset: {SAMPLE_DATASETS[self.state.dataset_name]['name']}")
        print(f"Summary: {self.state.final_insights['summary']}")
        print("\nTop 3 Prioritized Insights:")
        for i, insight in enumerate(self.state.final_insights['prioritized_insights'][:3], 1):
            print(f"{i}. {insight['insight']} (Priority: {insight['priority']})")
        print("\nRecommendations:")
        for i, rec in enumerate(self.state.final_insights['recommendations'][:3], 1):
            print(f"{i}. {rec}")
        print("========================\n")
        
        # Format the output based on the requested format
        if self.state.output_format.lower() == "json":
            # For JSON format, return the raw data structure
            return self.state.final_insights
        else:
            # For markdown format, convert the data to a formatted markdown string
            return self._format_as_markdown(self.state.final_insights)
    
    def _format_as_markdown(self, insights: Dict[str, Any]) -> str:
        """Format the insights as a markdown string."""
        dataset_name = SAMPLE_DATASETS[insights["dataset_analyzed"]]["name"]
        
        # Build the markdown output
        md = [
            f"# Analysis Results for {dataset_name}",
            "",
            f"*Analysis completed at: {insights['timestamp']}*",
            "",
            "## Summary",
            "",
            insights["summary"],
            "",
            "## Key Insights (Prioritized)",
            ""
        ]
        
        # Add prioritized insights
        for i, insight in enumerate(insights["prioritized_insights"], 1):
            md.append(f"{i}. **{insight['insight']}** *(Priority: {insight['priority']})*")
        
        md.append("")
        md.append("## Recommendations")
        md.append("")
        
        # Add recommendations
        for i, rec in enumerate(insights["recommendations"], 1):
            md.append(f"{i}. {rec}")
        
        # Join all lines with newlines
        return "\n".join(md)

async def kickoff(inputs: dict = None):
    """
    Kickoff function for the flow.
    This is the entry point for the flow when called from Kodosumi.
    """
    # Initialize Ray if not already initialized and not in Kodosumi environment
    if not ray.is_initialized() and not is_kodosumi:
        print("Initializing local Ray instance")
        ray.init()
    
    # Create the flow
    flow = CrewAIFlow()
    
    # Update state with inputs if provided
    if inputs and isinstance(inputs, dict):
        for key, value in inputs.items():
            if hasattr(flow.state, key):
                setattr(flow.state, key, value)
    
    # Run the flow
    result = await flow.kickoff_async()
    
    # Return the result
    return result

if __name__ == "__main__":
    """Main entry point for the flow when run directly."""
    # Parse command line arguments
    args = {}
    for arg in sys.argv[1:]:
        if "=" in arg:
            key, value = arg.split("=", 1)
            args[key] = value
    
    # Run the flow
    result = asyncio.run(kickoff(args))
    
    # Print the result
    print("\nFlow execution completed.")
    
    # Shutdown Ray if we initialized it
    if ray.is_initialized() and not is_kodosumi:
        print("Shutting down Ray...")
        ray.shutdown()
        print("Ray shutdown complete.") 