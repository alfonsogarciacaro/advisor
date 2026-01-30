import pytest
import datetime
from unittest.mock import AsyncMock, MagicMock
from app.services.news_service import NewsService

@pytest.mark.asyncio
async def test_news_service_cache_hit():
    mock_provider = AsyncMock()
    mock_storage = AsyncMock()
    mock_logger = MagicMock()
    
    # Setup mock storage with fresh news
    fresh_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
    mock_storage.get.return_value = {
        "news": [{"title": "Cached News"}],
        "updated_at": fresh_time
    }
    
    service = NewsService(provider=mock_provider, storage=mock_storage, logger=mock_logger, ttl_hours=12)
    news = await service.get_latest_news()
    
    assert len(news) == 1
    assert news[0]["title"] == "Cached News"
    mock_provider.get_news_summary.assert_not_called()

@pytest.mark.asyncio
async def test_news_service_cache_miss_old():
    mock_provider = AsyncMock()
    mock_storage = AsyncMock()
    mock_logger = MagicMock()
    
    # Setup mock storage with old news
    old_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=13)).isoformat()
    mock_storage.get.return_value = {
        "news": [{"title": "Old News"}],
        "updated_at": old_time
    }
    
    # Setup mock provider news
    mock_provider.get_news_summary.return_value = [{"title": "New News"}]
    
    service = NewsService(provider=mock_provider, storage=mock_storage, logger=mock_logger, ttl_hours=12)
    news = await service.get_latest_news()
    
    assert len(news) == 1
    assert news[0]["title"] == "New News"
    mock_provider.get_news_summary.assert_called_once()
    mock_storage.save.assert_called_once()

@pytest.mark.asyncio
async def test_news_service_cache_miss_none():
    mock_provider = AsyncMock()
    mock_storage = AsyncMock()
    mock_logger = MagicMock()
    
    # Setup mock storage with no news
    mock_storage.get.return_value = None
    
    # Setup mock provider news
    mock_provider.get_news_summary.return_value = [{"title": "Fresh News"}]
    
    service = NewsService(provider=mock_provider, storage=mock_storage, logger=mock_logger, ttl_hours=12)
    news = await service.get_latest_news()
    
    assert len(news) == 1
    assert news[0]["title"] == "Fresh News"
    mock_provider.get_news_summary.assert_called_once()
    mock_storage.save.assert_called_once()
