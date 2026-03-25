"""
WordPress Agent - Autonomous Service
Działa w tle, nasłuchuje zadań w Supabase, wykonuje na WordPress
"""
import os
import asyncio
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import httpx
from datetime import datetime

from wordpress_client import WordPressClient
from claude_planner import ClaudePlanner
from task_processor import TaskProcessor
from notifications import TelegramNotifier

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global task processor
task_processor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global task_processor
    
    # Startup
    logger.info("🚀 Starting WordPress Agent...")
    
    # Initialize components
    wp_client = WordPressClient(
        url=os.getenv("WP_URL", "https://www.sklep.linguachess.com"),
        username=os.getenv("WP_USERNAME"),
        password=os.getenv("WP_PASSWORD")
    )
    
    claude_planner = ClaudePlanner(
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )
    
    telegram_notifier = TelegramNotifier(
        bot_token=os.getenv("TELEGRAM_BOT_TOKEN", "8768280651:AAF7PtL_-zvJXffvQngTtgC_rqfPdzzZN0Y"),
        chat_id=os.getenv("TELEGRAM_CHAT_ID", "8149345223")
    )
    
    task_processor = TaskProcessor(
        wp_client=wp_client,
        claude_planner=claude_planner,
        notifier=telegram_notifier,
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_ANON_KEY")
    )
    
    # Start background task processing
    asyncio.create_task(task_processor.start())
    
    logger.info("✅ WordPress Agent ready!")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down WordPress Agent...")
    await task_processor.stop()

app = FastAPI(
    title="WordPress Agent",
    description="Autonomous WordPress management service",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "running",
        "service": "WordPress Agent",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "components": {
            "task_processor": task_processor.is_running if task_processor else False,
            "wordpress": await task_processor.wp_client.test_connection() if task_processor else False
        }
    }

@app.post("/task")
async def create_task(task_description: str):
    """Manually create a task (for testing)"""
    if not task_processor:
        raise HTTPException(status_code=503, detail="Task processor not initialized")
    
    task_id = await task_processor.create_task(task_description)
    return {
        "task_id": task_id,
        "description": task_description,
        "status": "queued"
    }

@app.get("/stats")
async def get_stats():
    """Get agent statistics"""
    if not task_processor:
        raise HTTPException(status_code=503, detail="Task processor not initialized")
    
    return await task_processor.get_stats()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
