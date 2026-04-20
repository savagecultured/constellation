from fastapi import FastAPI
from app.api.v1 import auth, admin, media
from app.core.config import settings

app = FastAPI(
    title="Constellation Streaming API",
    description="Backend control plane for media streaming platform",
    version="1.0.0"
)

# Include Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin API"])
app.include_router(media.router, prefix="/api/v1/media", tags=["Media API"])

@app.get("/health")
def health_check():
    return {"status": "ok", "environment": settings.ENVIRONMENT}