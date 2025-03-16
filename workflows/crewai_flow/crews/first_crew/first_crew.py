import os
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from crewai import Agent, Crew, Process, Task
from langchain_openai import ChatOpenAI

# Define your output model
class FirstCrewOutput(BaseModel):
    """
    Output model for the DataAnalysisCrew
    
    This model defines the structure of the output from the crew.
    The output can be formatted as either markdown (human-readable) or
    JSON (for agent-to-agent interactions) based on the flow's output_format parameter.
    """
    summary: str = Field(..., description="Summary of the data analysis")
    insights: List[str] = Field(..., description="Key insights from the analysis")
    recommendations: List[str] = Field(..., description="Recommendations based on the analysis")

class FirstCrew:
    """
    Data Analysis Crew.
    This crew analyzes data and provides insights and recommendations.
    """
    
    def __init__(self):
        """Initialize the crew with any necessary configuration"""
        # Initialize your LLM
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("Warning: OPENAI_API_KEY environment variable is not set. Using a mock LLM for testing.")
            # Use a mock LLM for testing
            from langchain.llms.fake import FakeListLLM
            
            # Create mock responses for data analysis and insights
            mock_responses = [
                # Response for the analysis task
                """
                Based on my analysis of the Quarterly Sales Data, here are the key patterns and trends:

                1. Electronics category shows strong performance, particularly in Q4 in the West region with sales of $145,000, which is the highest in the dataset.
                2. The North region consistently performs well in Electronics sales across quarters, with $125,000 in Q1 and $132,000 in Q2.
                3. Furniture sales are concentrated in the East (Q1: $118,000) and South (Q2: $97,000) regions.
                4. Clothing sales appear in the West (Q1: $92,000) and East (Q3: $105,000) regions.
                5. There's a noticeable quarterly progression in Electronics sales, with the highest sales occurring in Q4.
                6. The South region has the lowest Electronics sales in Q1 at $87,000.
                7. The dataset shows regional specialization in product categories.
                8. Overall, Electronics appears to be the strongest performing category across regions.

                This analysis reveals both regional preferences and seasonal trends in sales performance.
                """,
                
                # Response for the insights task
                """
                Based on the data analysis provided, here are the business insights and recommendations:

                Summary:
                The quarterly sales data reveals distinct regional preferences for product categories, with Electronics showing the strongest overall performance, particularly in Q4. The North region consistently performs well in Electronics sales, while Furniture and Clothing sales vary by region and quarter.

                Key Business Insights:
                1. Electronics is the highest-performing category, with peak sales in Q4 in the West region.
                2. Regional specialization exists - North excels in Electronics, East in Furniture and Clothing, South in Electronics and Furniture, and West in Electronics and Clothing.
                3. Seasonal trends are evident, with Q4 showing the highest sales for Electronics.
                4. The North region demonstrates consistent performance across quarters.
                5. There's potential for growth in underperforming category-region combinations.

                Actionable Recommendations:
                1. Increase Electronics inventory in all regions for Q4 to capitalize on seasonal demand.
                2. Develop targeted marketing campaigns for Electronics in the West region to build on existing strength.
                3. Investigate why South region has lower Electronics sales and implement improvement strategies.
                4. Consider expanding Furniture offerings in the East and South regions where they perform well.
                5. Implement cross-selling strategies in regions with single-category strength.
                6. Develop a Q4 promotional strategy for Electronics across all regions.
                7. Conduct customer research in high-performing regions to identify success factors that can be applied elsewhere.
                """
            ]
            
            self.llm = FakeListLLM(responses=mock_responses)
        else:
            # Use the real OpenAI LLM
            self.llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0.2,
                api_key=api_key
            )
    
    def crew(self) -> Crew:
        """
        Create and return the crew.
        This method is called by the flow to get the crew.
        """
        # Create agents
        data_analyst = Agent(
            name="Data Analyst",
            role="Senior Data Analyst",
            goal="Analyze data and extract meaningful patterns",
            backstory="You are an experienced data analyst with expertise in finding patterns and insights in various types of data.",
            llm=self.llm,
            verbose=True
        )
        
        insights_specialist = Agent(
            name="Insights Specialist",
            role="Business Insights Specialist",
            goal="Convert data analysis into actionable business insights",
            backstory="You specialize in translating technical data findings into business insights and recommendations that can drive decision-making.",
            llm=self.llm,
            verbose=True
        )
        
        # Create tasks
        analysis_task = Task(
            name="Analyze Data",
            agent=data_analyst,
            description="""
            Analyze the following data and identify key patterns and trends:
            
            Dataset: {dataset_name}
            Description: {dataset_description}
            Sample data points: {sample_data}
            
            Provide a detailed analysis of the patterns and trends you observe.
            """,
            expected_output="A detailed analysis of the data with identified patterns and trends"
        )
        
        insights_task = Task(
            name="Generate Insights and Recommendations",
            agent=insights_specialist,
            description="""
            Based on the data analysis provided, generate business insights and actionable recommendations.
            
            Analysis: {{analysis_task.output}}
            
            Provide:
            1. A summary of the analysis
            2. Key business insights
            3. Actionable recommendations
            """,
            context=[analysis_task],
            expected_output="Business insights and actionable recommendations based on the data analysis"
        )
        
        # Create and return the crew
        return Crew(
            agents=[data_analyst, insights_specialist],
            tasks=[analysis_task, insights_task],
            process=Process.sequential,
            verbose=True
        ) 