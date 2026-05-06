from pathlib import Path
import sys

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Allow `python backend/app/main.py` to work by exposing the backend package root.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api.routes.analysis import router as analysis_router
from app.api.routes.users import router as users_router
from app.core.config import get_settings
from app.core.errors import AppError
from app.services.store import store


def create_app() -> FastAPI:
    settings = get_settings()
    store.ensure_ready()
    project_root = Path(__file__).resolve().parents[2]
    frontend_dir = project_root / "frontend"
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Production-minded backend for resume optimization and job matching.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.code, "message": exc.message},
        )

    @app.get("/api/v1/health", tags=["health"])
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(analysis_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1")
    if frontend_dir.exists():
        def frontend_file(path: Path) -> FileResponse:
            return FileResponse(
                path,
                headers={
                    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                    "Pragma": "no-cache",
                },
            )

        @app.get("/", include_in_schema=False)
        def serve_frontend_root() -> FileResponse:
            return frontend_file(frontend_dir / "index.html")

        @app.get("/{path:path}", include_in_schema=False)
        def serve_frontend_app(path: str) -> FileResponse:
            target = frontend_dir / path
            if target.exists() and target.is_file():
                return frontend_file(target)
            return frontend_file(frontend_dir / "index.html")

        app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
