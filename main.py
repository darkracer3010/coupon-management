from fastapi import FastAPI
from app.router import router
from app.db import init_db

app = FastAPI(
    title="Coupon Management API",
    description="RESTful API for managing and applying discount coupons",
    version="1.0.0"
)

# Initialize database
init_db()

# Include routers
app.include_router(router)


@app.get("/")
async def root():
    return {
        "message": "Coupon Management API",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
