from typing import Callable

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.platform.exceptions import AppException


def create_app(*, lifespan: Callable) -> FastAPI:
    app = FastAPI(
        title="JChat CRM API",
        description="Backend Multi-Tenant para automatización de citas y mensajería en canales de Meta.",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # En producción se debe restringir a los dominios permitidos
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppException)
    async def app_exception_handler(request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": {"code": exc.code, "message": exc.message}},
        )

    return app
