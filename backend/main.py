import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from features.simulation.router import router as simulation_router

app = FastAPI(
    title="ASHPB PV ESS Visualization API",
    description="API to serve downsampled simulation data for visualization.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 단일 서비스로 서빙하므로 same-origin — Railway URL도 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(simulation_router, prefix="/api/v1/simulation", tags=["Simulation"])

# ── 프론트엔드 정적 파일 서빙 ──────────────────────────────────────
# Railway 컨테이너 내부 경로: /app/frontend/build
FRONTEND_BUILD = os.path.join(os.path.dirname(__file__), "..", "frontend", "build")

if os.path.isdir(FRONTEND_BUILD):
    # SPA 라우팅: /*  →  index.html 폴백
    app.mount("/", StaticFiles(directory=FRONTEND_BUILD, html=True), name="static")
else:
    @app.get("/")
    def read_root():
        return {"status": "ok", "note": "frontend build not found"}
