from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, preferences, chatbot
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="KindaLike API",
    description="Restaurant Recommender System API",
    version="1.0.0"
)

# CORS middleware to allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(preferences.router)
app.include_router(chatbot.router)

@app.get("/")
async def root():
    return {"message": "Welcome to KindaLike API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 5000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
