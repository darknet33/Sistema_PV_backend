import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import api_router
from app.database import init_db, Base
from app.models import Base
from app.ws import init_loop

init_db()

app = FastAPI(
    title="Sistema RHINO API",
    description="API para sistema de inventario con FastAPI",
    version="3.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.on_event("startup")
async def startup():
    init_loop(asyncio.get_running_loop())


@app.get("/")
def read_root():
    return {"message": "Sistema RHINO API v3.0", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
