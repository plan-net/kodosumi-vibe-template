"""
Example showing how to use the ExaSearchTool with CrewAI.

This example demonstrates how to create a simple flow with CrewAI
that uses the ExaSearchTool to search for information.
"""

import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew
from workflows.tools.exa_search import ExaSearchTool

# Load environment variables (make sure EXA_API_KEY is set)
load_dotenv()

def main():
    """Run a simple CrewAI workflow using the ExaSearchTool."""
    
    # Create the Exa search tool
    exa_search_tool = ExaSearchTool(
        timeout=15,       # Request timeout in seconds
        max_retries=3,    # Maximum number of retries for failed requests
        retry_delay=2     # Delay between retries in seconds
    )
    
    # Create a researcher agent with the search tool
    researcher = Agent(
        role="Research Specialist",
        goal="Find accurate and up-to-date information on specified topics",
        backstory="""You are a skilled researcher with expertise in finding and analyzing 
        information from the web. You are meticulous and always provide comprehensive results.""",
        tools=[exa_search_tool],
        verbose=True
    )
    
    # Create an analyst agent
    analyst = Agent(
        role="Information Analyst",
        goal="Analyze information and provide clear insights",
        backstory="""You are an expert analyst who can identify key trends and insights from 
        research data. You excel at summarizing complex information into actionable insights.""",
        verbose=True
    )
    
    # Create research task
    research_task = Task(
        description="""
        Research the latest advancements in artificial intelligence for 2024.
        Focus on breakthroughs in language models, computer vision, and robotics.
        Be specific and include examples of real-world applications.
        Provide at least 3 major breakthroughs with sources.
        """,
        agent=researcher
    )
    
    # Create analysis task
    analysis_task = Task(
        description="""
        Analyze the research findings on AI advancements and create a summary of key trends.
        Identify which areas of AI are seeing the most rapid progress.
        Suggest potential implications for business and society.
        Format your response as a clear, concise report.
        """,
        agent=analyst,
        context=[research_task]  # Use output from research task as context
    )
    
    # Create a crew with the agents and tasks
    crew = Crew(
        agents=[researcher, analyst],
        tasks=[research_task, analysis_task],
        verbose=True
    )
    
    # Run the crew
    print("Starting CrewAI workflow with ExaSearchTool...")
    result = crew.kickoff()
    
    print("\n=== Final Result ===")
    print(result)

if __name__ == "__main__":
    main() 