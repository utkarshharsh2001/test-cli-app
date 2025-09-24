from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.endpoints import router
from app.models.database import create_tables

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_tables()
    yield
    # Shutdown (if needed)

# Create FastAPI app
app = FastAPI(
    title="Levo CLI API - Schema Upload and Versioning",
    description="API for uploading, versioning, and managing OpenAPI schemas",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "Levo CLI API - Schema Upload and Versioning Service"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "levo-cli-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
