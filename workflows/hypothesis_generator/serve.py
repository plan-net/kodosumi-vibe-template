from pathlib import Path

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from kodosumi.serve import Launch, ServeAPI
from ray.serve import deployment, ingress

app = ServeAPI()

templates = Jinja2Templates(directory=Path(__file__).parent.joinpath("templates"))


@deployment
@ingress(app)
class HypothesisGeneratorService:
    """
    Service for the Hypothesis Generator flow.
    This class handles the HTTP requests and responses.
    """

    @app.get(
        "/",
        name="Hypothesis Generator",
        description="Generate marketing hypotheses for products based on target audience and goals.",
    )
    async def get(self, request: Request) -> HTMLResponse:
        """
        Handle GET requests.
        Returns the HTML form for submitting parameters.
        """
        return templates.TemplateResponse(request=request, name="form.html", context={})

    @app.post("/", response_model=None)
    async def post(self, request: Request):
        """
        Handle POST requests.
        Extracts parameters from the form and launches the flow.
        """
        form_data = await request.form()
        return Launch(
            request,
            "workflows.hypothesis_generator.main:kickoff",
            {
                "brand": form_data.get("brand", ""),
                "product": form_data.get("product", ""),
                "audience": form_data.get("audience", ""),
                "goal": form_data.get("goal", ""),
                "output_format": form_data.get("output_format", "markdown"),
            },
        )


# Bind the service to Ray Serve
fast_app = HypothesisGeneratorService.bind()  # type: ignore
