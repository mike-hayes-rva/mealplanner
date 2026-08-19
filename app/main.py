from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, recipes, tags

app = FastAPI(title="Meal Planner API", version="0.1.0")

# Wide open for local dev (React Native / simulator / physical device).
# Tighten this once you have a real deployed frontend origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(recipes.router)
app.include_router(tags.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
