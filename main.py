from fastapi import FastAPI

from database import engine
from loguru import logger
from models import Base
from routers import analytics, comments, poshts, users

logger.add("loguru/main.log")

logger.info("This is the main.py that is running!")
app = FastAPI()


@app.on_event("startup")
async def on_startup() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


app.include_router(users.router)

app.include_router(poshts.router)

app.include_router(comments.router)

app.include_router(analytics.router)

logger.info("ROUTES:")

for route in app.routes:
    logger.info(f"{route.path} [{route.methods}]")


@app.get("/")
async def root() -> dict:
    return {"status": "ok"}
