import asyncio
import json
import logging
from datetime import datetime
from fastapi import APIRouter, Request, Depends
from starlette.responses import StreamingResponse

from utils.event_broadcaster import broadcaster
from api.middleware.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Events"])


@router.get("/sse")
async def event_stream(request: Request, current_user: dict = Depends(get_current_user)):
    logger.info(f"SSE client connecting: {current_user['login']}")
    queue = asyncio.Queue()
    await broadcaster.connect(queue)
    
    logger.info(f"SSE client connected: {current_user['login']}")
    
    async def generator():
        try:
            # Отправляем приветственное сообщение
            yield f"event: connected\ndata: {json.dumps({'status': 'ok', 'user': current_user['login']})}\n\n"
            
            while True:
                # Проверяем, не отключился ли клиент
                if await request.is_disconnected():
                    logger.info(f"Client disconnected: {current_user['login']}")
                    break
                
                # Ждём сообщение с таймаутом (heartbeat)
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=15.0)
                    
                    # Безопасное извлечение event и data
                    event = message.get('event', 'unknown')
                    data = message.get('data', message)  # если нет 'data', отправляем всё сообщение
                    
                    # Форматируем SSE сообщение
                    yield f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"
                    
                except asyncio.TimeoutError:
                    # Отправляем heartbeat, чтобы соединение не закрылось
                    yield f"event: heartbeat\ndata: {json.dumps({'timestamp': datetime.now().isoformat()})}\n\n"
                    
        except asyncio.CancelledError:
            logger.info(f"SSE generator cancelled for user: {current_user['login']}")
        except Exception as e:
            logger.error(f"Unexpected error in SSE generator: {e}")
        finally:
            broadcaster.disconnect(queue)
            logger.info(f"SSE client disconnected: {current_user['login']}")
    
    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )