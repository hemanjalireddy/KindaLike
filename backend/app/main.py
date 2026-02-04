from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, chatbot, preference_extraction
import os
from dotenv import load_dotenv
from loguru import logger


load_dotenv()

# Configure logging
logger.add(
    "logs/kindalike_{time}.log",
    rotation="1 day",
    retention="7 days",
    level="INFO"
)

app = FastAPI(
    title="KindaLike API",
    description="Restaurant Recommender System API - Phase 3: Preference Extraction Engine",
    version="3.0.0"
)

# CORS middleware to allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(preference_extraction.router)  # Phase 3: New preference extraction
app.include_router(chatbot.router, prefix="/api/chat", tags=["Chatbot"])

@app.get("/")
async def root():
    return {"message": "Welcome to KindaLike API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

print("\n🔥 AVAILABLE ROUTES 🔥")
for route in app.routes:
    if hasattr(route, "path"):
        print(f"➡️  {route.methods} {route.path}")
print("----------------------\n")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 5000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
