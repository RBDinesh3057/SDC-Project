from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from . import models
from .database import engine
from .routes import router

# Create DB tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="FitBuddy AI Workout Generator")

# Mount Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include Application Routes
app.include_router(router)
