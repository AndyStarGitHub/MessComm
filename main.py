from fastapi import FastAPI

from database import engine
from models import Base
from routers import users, poshts, comments, analytics

print("🔥 This is the main.py that is running!")
app = FastAPI()

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


app.include_router(users.router)

app.include_router(poshts.router)

app.include_router(comments.router)

app.include_router(analytics.router)

print("🔥 ROUTES 20250802:")
for route in app.routes:
    print(f"{route.path} [{route.methods}]")

@app.get("/")
async def root():
    return {"status": "ok"}
