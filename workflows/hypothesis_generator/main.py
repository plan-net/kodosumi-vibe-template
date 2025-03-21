#!/usr/bin/env python

import asyncio
import os
import sys
import time
from typing import Any, Dict, List

from crewai.flow import Flow, listen, start
from dotenv import load_dotenv
from pydantic import BaseModel

from workflows.common.formatters import extract_structured_data, format_output
from workflows.common.logging_utils import get_logger
from workflows.common.processors import handle_flow_error
from workflows.common.utils import initialize_ray, shutdown_ray

# Import your crew classes here
from workflows.hypothesis_generator.crews.hypothesis_crew.hypothesis_crew import (
    HypothesisCrew,
)

# Set up logger
logger = get_logger(__name__)

# Load environment variables from .env file
load_dotenv()

# Check if we're running in Kodosumi environment
# Kodosumi will handle Ray initialization for us
is_kodosumi = os.environ.get("KODOSUMI_ENVIRONMENT") == "true"


class HypothesisGeneratorState(BaseModel):
    """
    Define the flow state for hypothesis generation.
    This will hold all the data that is passed between steps in the flow.
    """

    brand: str = ""  # Name of the company
    product: str = ""  # Product or service name
    audience: str = ""  # Description of target audience
    goal: str = ""  # Goal to achieve
    output_format: str = "markdown"  # Default output format (markdown or json)
    research_results: Dict[str, Any] = {}
    obvious_hypotheses: List[Dict[str, Any]] = []
    innovative_hypotheses: List[Dict[str, Any]] = []
    final_results: Dict[str, Any] = {}


class HypothesisGeneratorFlow(Flow[HypothesisGeneratorState]):
    """
    Define your flow steps here.
    Each step is a method decorated with @listen that takes the output of a previous step.
    """
    
    def _validate_source_citations(self):
        """Validate that hypotheses properly cite sources from the research."""
        source_ids = {source.get("id") for source in self.state.research_results.get("sources", [])}
        if not source_ids:
            logger.warning("No source IDs found in research results, cannot validate citations")
            return
            
        logger.info(f"Validating source citations against {len(source_ids)} available sources")
        
        for hypothesis_type in ["obvious_hypotheses", "innovative_hypotheses"]:
            hypotheses = getattr(self.state, hypothesis_type, [])
            for i, hypothesis in enumerate(hypotheses):
                cited_sources = hypothesis.get("sources", [])
                invalid_sources = [s for s in cited_sources if s not in source_ids]
                if invalid_sources:
                    logger.warning(f"{hypothesis_type.capitalize()} #{i+1} cites invalid sources: {invalid_sources}")
                if not cited_sources:
                    logger.warning(f"{hypothesis_type.capitalize()} #{i+1} does not cite any sources")

    @start()
    def validate_inputs(self):
        """
        Validate the inputs to the flow.
        This is the first step in the flow.
        """
        logger.info("Validating inputs...")

        # Check required inputs
        missing_inputs = []
        if not self.state.brand:
            missing_inputs.append("brand")
        if not self.state.product:
            missing_inputs.append("product")
        if not self.state.audience:
            missing_inputs.append("audience")
        if not self.state.goal:
            missing_inputs.append("goal")

        if missing_inputs:
            logger.warning(f"Missing required inputs: {', '.join(missing_inputs)}")
            return handle_flow_error(
                self.state,
                self.state.output_format,
                error=f"Missing required inputs: {', '.join(missing_inputs)}",
            )

        logger.info(f"Brand: {self.state.brand}")
        logger.info(f"Product: {self.state.product}")
        logger.info(f"Audience: {self.state.audience}")
        logger.info(f"Goal: {self.state.goal}")

    @listen(validate_inputs)
    def generate_hypotheses(self):
        """
        Generate hypotheses using CrewAI.

        This step creates a crew of AI agents to:
        1. Research relevant information using exa.ai
        2. Generate obvious hypotheses
        3. Generate innovative hypotheses

        The structured output from the crew is stored in the flow state.
        """
        try:
            logger.info(
                f"Using CrewAI to generate hypotheses for {self.state.brand} "
                f"{self.state.product}..."
            )

            # Create and run the crew
            crew_instance = HypothesisCrew()
            crew = crew_instance.crew()

            # Prepare the task inputs
            task_inputs = {
                "brand": self.state.brand,
                "product": self.state.product,
                "audience": self.state.audience,
                "goal": self.state.goal,
            }

            # Run the crew and get the result
            crew_result = crew.kickoff(inputs=task_inputs)

            # Extract structured data from the crew result
            json_data = extract_structured_data(crew_result)

            if json_data:
                # Store the structured output in the state
                research_results = json_data.get("research", {})
                sources = research_results.get("sources", [])
                
                # Validate research results
                if len(sources) < 5:
                    logger.warning(f"Research only produced {len(sources)} sources, which is below the minimum recommendation of 10")
                
                # Check for source IDs
                for i, source in enumerate(sources):
                    if 'id' not in source:
                        source['id'] = f"S{i+1}"  # Add auto-generated IDs if missing
                
                self.state.research_results = research_results
                self.state.obvious_hypotheses = json_data.get("obvious_hypotheses", [])
                self.state.innovative_hypotheses = json_data.get(
                    "innovative_hypotheses", []
                )
                
                # Validate source citations
                self._validate_source_citations()
                
                logger.info("CrewAI hypothesis generation completed successfully.")
                return self.finalize_results
            else:
                logger.error("No structured output available from the crew.")
                return handle_flow_error(self.state, self.state.output_format)
        except Exception as e:
            logger.error(
                f"Error during CrewAI hypothesis generation: {e}", exc_info=True
            )
            return handle_flow_error(self.state, self.state.output_format, error=e)

    @listen(generate_hypotheses)
    def finalize_results(self):
        """
        Final step in the flow.
        This step aggregates the results from previous steps.
        """
        logger.info("Finalizing results...")

        # Combine all results into the final structure
        self.state.final_results = {
            "brand": self.state.brand,
            "product": self.state.product,
            "audience": self.state.audience,
            "goal": self.state.goal,
            "research_summary": self.state.research_results.get(
                "summary", 
                "No research summary available"
            ),
            "sources": self.state.research_results.get("sources", []),
            "obvious_hypotheses": self.state.obvious_hypotheses,
            "innovative_hypotheses": self.state.innovative_hypotheses,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        logger.info("Flow completed successfully!")

        # Format the output based on the requested format
        return format_output(self.state.final_results, self.state.output_format)


async def kickoff(inputs: dict = None):
    """
    Kickoff function for the flow.
    This is the entry point for the flow when called from Kodosumi.
    """
    # Initialize Ray if needed
    initialize_ray(is_kodosumi)

    # Create the flow
    flow = HypothesisGeneratorFlow()

    # Update state with inputs if provided
    if inputs and isinstance(inputs, dict):
        logger.info(f"Initializing flow with inputs: {inputs}")
        for key, value in inputs.items():
            if hasattr(flow.state, key):
                setattr(flow.state, key, value)
            else:
                logger.warning(f"Ignoring unknown input parameter: {key}")

    try:
        # Run the flow
        logger.info("Starting flow execution...")
        result = await flow.kickoff_async()
        logger.info("Flow execution completed successfully")
        return result
    except Exception as e:
        logger.error(f"Error during flow execution: {e}", exc_info=True)
        # Return a fallback response in case of error
        return format_output(
            {
                "error": str(e), 
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "markdown",
        )
    finally:
        # Shutdown Ray if needed
        shutdown_ray(is_kodosumi)


if __name__ == "__main__":
    """Main entry point for the flow when run directly."""
    try:
        # Parse command line arguments
        args = {}
        for arg in sys.argv[1:]:
            if "=" in arg:
                key, value = arg.split("=", 1)
                args[key] = value

        logger.info(f"Starting flow with command line arguments: {args}")

        # Run the flow
        result = asyncio.run(kickoff(args))

        # Print the result
        logger.info("Flow execution completed.")
        print("\n" + result)
    except Exception as e:
        logger.error(f"Error in main execution: {e}", exc_info=True)
        print(f"\nError: {e}")
        sys.exit(1)
