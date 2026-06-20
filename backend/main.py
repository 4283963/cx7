from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router

app = FastAPI(
    title="动态打包折扣最优组合仿真工具",
    description="机票与酒店动态打包折扣的多目标优化推荐API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "message": "动态打包折扣最优组合仿真工具 API",
        "version": "1.0.0",
        "docs": "/docs"
    }
