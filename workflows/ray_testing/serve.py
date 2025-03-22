#!/usr/bin/env python

import os
from kodosumi.serve import serve
from kodosumi.dtypes import Form, Select
from kodosumi.tracer import markdown

from workflows.ray_testing.main import kickoff

STATIC_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../workflows/common/static")

def get_docs():
    """Return documentation for the workflow"""
    return """
    # Ray Testing Workflow
    
    This workflow allows you to test different Ray features within the Kodosumi environment.
    
    ## Available Tests
    
    - **Basic Test**: Simple Ray tasks and remote functions
    - **Parallel Test**: Process data in parallel with Ray workers
    - **Actor Test**: Stateful processing with Ray actors
    
    ## Purpose
    
    This workflow helps debug and understand Ray's behavior in different modes and configurations within Kodosumi.
    """

def get_form():
    """Return the form for the workflow"""
    return Form(
        title="Ray Testing",
        description="Select which Ray test to run",
        fields=[
            Select(
                id="test_name",
                label="Ray Test",
                description="Choose which Ray test to execute",
                options=[
                    {"value": "basic", "label": "Basic Test - Remote Functions"},
                    {"value": "parallel", "label": "Parallel Test - Worker Pattern"},
                    {"value": "actor", "label": "Actor Test - Stateful Processing"}
                ],
                default="basic"
            )
        ]
    )

@serve(name="Ray Testing Workflow", 
       description="Test different Ray features and patterns",
       form=get_form,
       docs=get_docs,
       static_folder=STATIC_FOLDER)
def entrypoint(inputs):
    """Entrypoint for the Ray testing Kodosumi workflow"""
    markdown("**Starting Ray Testing Workflow...**")
    return kickoff(inputs)

if __name__ == "__main__":
    entrypoint({"test_name": "basic"}) 