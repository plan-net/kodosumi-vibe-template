from pathlib import Path

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from ray.serve import deployment, ingress

from kodosumi.serve import Launch, ServeAPI


app = ServeAPI()

templates = Jinja2Templates(
    directory=Path(__file__).parent.joinpath("templates"))

# Available datasets for the dropdown
AVAILABLE_DATASETS = {
    "sales_data": "Quarterly Sales Data",
    "customer_feedback": "Customer Feedback Survey"
}

@deployment
@ingress(app)
class CrewAIFlowService:
    """
    Service for the CrewAI flow.
    This class handles the HTTP requests and responses.
    """

    @app.get("/", 
             name="Data Analysis Flow", 
             description="Execute a data analysis flow with the selected dataset.")
    async def get(self, request: Request) -> HTMLResponse:
        """
        Handle GET requests.
        Returns the HTML form for submitting parameters.
        """
        return templates.TemplateResponse(
            request=request, 
            name="form.html", 
            context={"datasets": AVAILABLE_DATASETS}
        )

    @app.post("/", response_model=None)
    async def post(self, request: Request):
        """
        Handle POST requests.
        Extracts parameters from the form and launches the flow.
        """
        form_data = await request.form()
        
        # Extract dataset selection from the form
        dataset_name = str(form_data.get("dataset_name", "sales_data"))
        
        # Validate dataset
        if dataset_name not in AVAILABLE_DATASETS:
            dataset_name = "sales_data"  # Default to sales_data if invalid
        
        # Launch the flow with the selected dataset
        return Launch(request, "workflows.crewai_flow.main:kickoff", {
            "dataset_name": dataset_name
        })

# Bind the service to Ray Serve
fast_app = CrewAIFlowService.bind()  # type: ignore 