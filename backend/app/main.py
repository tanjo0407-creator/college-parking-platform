import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import Base, SessionLocal, engine
from .routers import campus, parking, simulation, users, visitors
from .seed_data import init_db_and_seed
from .websocket_manager import ws_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist and seed initial data
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        init_db_and_seed(db)
    finally:
        db.close()
    yield
    # Shutdown logic if needed


app = FastAPI(
    title="College Campus Parking Management Platform",
    description="Interactive Campus Parking System with live spot tracking, rule-based spot allocation, and secure occupant RBAC.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local development and client integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(campus.router)
app.include_router(parking.router)
app.include_router(visitors.router)
app.include_router(users.router)
app.include_router(simulation.router)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; accept any incoming ping/messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


# Serve Frontend Static Files
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))
