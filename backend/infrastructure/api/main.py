"""Main entry point for the FastAPI application."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from infrastructure.config import ConfigError, load_env_file
from adapters.controllers.research_controller import router
from infrastructure.api.dependencies import setup_dependencies
from domain.exceptions import DomainError


def create_app() -> FastAPI:
    """App factory that builds the FastAPI application."""
    # Load .env into os.environ so config loaders can find the keys
    load_env_file()

    app = FastAPI(
        title="A.L.I.E. Research Agent",
        description="Phase 8 FastAPI Service",
        version="0.1.0"
    )
    
    # Include the router
    app.include_router(router)
    
    # Setup dependency injection
    setup_dependencies(app)
    
    # Add exception handlers
    @app.exception_handler(ConfigError)
    async def config_error_handler(request: Request, exc: ConfigError):
        return JSONResponse(
            status_code=503,
            content={"detail": f"Service unavailable due to misconfiguration: {str(exc)}"}
        )
        
    return app

# Instantiate the app so the FastAPI CLI can discover it automatically
app = create_app()
