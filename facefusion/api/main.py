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

    # Servir os arquivos estáticos do frontend Next.js exportado se existir
    import os
    import sys
    from fastapi.staticfiles import StaticFiles
    
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(backend_dir, "..", ".."))
    frontend_out_dir = os.path.join(root_dir, "frontend", "out")
    
    is_testing = "pytest" in sys.modules or "unittest" in sys.modules
    
    if os.path.exists(frontend_out_dir) and not is_testing:
        app.mount("/", StaticFiles(directory=frontend_out_dir, html=True), name="frontend")
    else:
        @app.get("/")
        def read_root():
            return {
                "app": "FaceFusion API",
                "version": "3.6.1",
                "status": "online"
            }

    return app


app = create_app()


def find_free_port(start_port: int = 8000, max_attempts: int = 100) -> int:
    import socket
    for p in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    raise RuntimeError(f"Nenhuma porta livre encontrada a partir de {start_port}")


def write_frontend_config(port: int) -> None:
    import os
    import json
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(backend_dir, "..", ".."))
    frontend_public_dir = os.path.join(root_dir, "frontend", "public")
    frontend_out_dir = os.path.join(root_dir, "frontend", "out")
    
    config_data = {"apiUrl": f"http://localhost:{port}"}
    
    if os.path.exists(frontend_public_dir):
        config_path = os.path.join(frontend_public_dir, "config.json")
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4)
            print(f"[API] Gravado config.json do frontend em: {config_path}", flush=True)
        except Exception as e:
            print(f"[API] Erro ao gravar config.json em public: {str(e)}", flush=True)
            
    if os.path.exists(frontend_out_dir):
        config_path = os.path.join(frontend_out_dir, "config.json")
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4)
            print(f"[API] Gravado config.json do frontend em: {config_path}", flush=True)
        except Exception as e:
            print(f"[API] Erro ao gravar config.json em out: {str(e)}", flush=True)


if __name__ == "__main__":
    # Carregar configuração padrão ou via variáveis de ambiente
    host = "127.0.0.1"
    try:
        port = find_free_port(8000)
    except Exception:
        port = 8000
        
    write_frontend_config(port)
    uvicorn.run("facefusion.api.main:app", host=host, port=port, reload=True)
