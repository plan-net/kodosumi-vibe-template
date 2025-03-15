from pathlib import Path

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from ray.serve import deployment, ingress

from kodosumi.serve import Launch, ServeAPI


app = ServeAPI()

templates = Jinja2Templates(
    directory=Path(__file__).parent.joinpath("templates"))

@deployment
@ingress(app)
class CrewAIFlowService:
    """
    Service for the CrewAI flow.
    This class handles the HTTP requests and responses.
    """

    @app.get("/", 
             name="CrewAI Flow", 
             description="Execute a CrewAI flow with the given parameters.")
    async def get(self, request: Request) -> HTMLResponse:
        """
        Handle GET requests.
        Returns the HTML form for submitting parameters.
        """
        return templates.TemplateResponse(
            request=request, name="form.html", context={})

    @app.post("/", response_model=None)
    async def post(self, request: Request):
        """
        Handle POST requests.
        Extracts parameters from the form and launches the flow.
        """
        form_data = await request.form()
        
        # Extract parameters from the form
        # Modify this to match your flow's parameters
        param1 = str(form_data.get("input_param1", ""))
        param2 = str(form_data.get("input_param2", ""))
        
        # Validate parameters
        if param1.strip() and param2.strip():
            # Launch the flow with the parameters
            return Launch(request, "crewai_flow.main:kickoff", {
                "input_param1": param1,
                "input_param2": param2
            })
        
        # If parameters are invalid, return the form again
        return await self.get(request)

# Bind the service to Ray Serve
fast_app = CrewAIFlowService.bind()  # type: ignore 