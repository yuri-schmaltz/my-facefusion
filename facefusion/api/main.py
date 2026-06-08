import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from facefusion.app_context import set_app_context
set_app_context('cli')

from facefusion import state_manager
from facefusion.program import create_program
from facefusion.args import apply_args
from facefusion.jobs import job_manager

# Inicializar o state_manager com os argumentos padrão
program = create_program()
args = vars(program.parse_args(['run']))
apply_args(args, state_manager.init_item)

# Inicializar a fila de jobs
jobs_path = state_manager.get_item('jobs_path') or '.jobs'
job_manager.init_jobs(jobs_path)

from facefusion.api.database import init_db
from facefusion.api.worker import start_worker, stop_worker
from facefusion.api.routes import router as api_router
from contextlib import asynccontextmanager


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        init_db()
        start_worker()
        yield
        stop_worker()

    app = FastAPI(
        title="FaceFusion API",
        description="RESTful API for the modernized FaceFusion decoupled architecture",
        version="3.6.1",
        lifespan=lifespan
    )


    @app.middleware("http")
    async def log_correlation_middleware(request, call_next):
        import uuid
        from facefusion.logger import set_session_context
        session_id = request.headers.get("X-Session-ID") or request.headers.get("X-Correlation-ID") or f"sess-{uuid.uuid4().hex[:8]}"
        set_session_context(session_id)
        try:
            response = await call_next(request)
            response.headers["X-Session-ID"] = session_id
            return response
        finally:
            set_session_context('')

    # Configuração de CORS para permitir acesso seguro do frontend Next.js local em qualquer porta
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Inclusão do roteador de endpoints
    app.include_router(api_router, prefix="/api")

    @app.get("/")
    def read_root():
        return {
            "app": "FaceFusion API",
            "version": "3.6.1",
            "status": "online"
        }

    return app


app = create_app()


if __name__ == "__main__":
    # Carregar configuração padrão ou via variáveis de ambiente
    host = "127.0.0.1"
    port = 8000
    uvicorn.run("facefusion.api.main:app", host=host, port=port, reload=True)
