from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from app.services.news_service import NewsService
from app.core.dependencies import get_news_service, get_logger
from app.services.logger_service import LoggerService

router = APIRouter()

@router.get("", response_model=List[Dict[str, Any]])
async def get_news(
    news_service: NewsService = Depends(get_news_service),
    logger: LoggerService = Depends(get_logger)
):
    return await news_service.get_latest_news()
