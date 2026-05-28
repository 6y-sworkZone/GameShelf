from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import games, progress, wishlist, achievements, statistics, friends, annual

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="游戏库存管理系统 - GameShelf",
    description="管理你的游戏库存、进度、成就和开销统计",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(games.router)
app.include_router(progress.router)
app.include_router(wishlist.router)
app.include_router(achievements.router)
app.include_router(statistics.router)
app.include_router(friends.router)
app.include_router(annual.router)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "GameShelf API 运行正常"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765)
