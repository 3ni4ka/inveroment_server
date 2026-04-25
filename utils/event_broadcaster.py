"""
Broadcaster for Server-Sent Events (SSE)
"""

import asyncio
from typing import List, Any
import logging

logger = logging.getLogger(__name__)


class Broadcaster:
    """Manages SSE connections and broadcasts messages to all clients."""
    
    def __init__(self):
        logger.info("Initializing Broadcaster...")
        self._queues: List[asyncio.Queue] = []
        self._lock = asyncio.Lock()
    
    async def connect(self, queue: asyncio.Queue):
        """Add a new client queue to the list of active connections."""
        async with self._lock:
            self._queues.append(queue)
            logger.info(f"SSE client connected. Total clients: {len(self._queues)}")
    
    def disconnect(self, queue: asyncio.Queue):
        """Remove a client queue from the list of active connections."""
        if queue in self._queues:
            self._queues.remove(queue)
            logger.info(f"SSE client disconnected. Total clients: {len(self._queues)}")
    
    async def broadcast(self, message: Any):
        """Send a message to all connected clients."""
        logger.info(f"Broadcasting message to {self.clients_count} clients: {message}")
        async with self._lock:
            disconnected = []
            for queue in self._queues:
                try:
                    await queue.put(message)
                except Exception as e:
                    logger.warning(f"Failed to send to client: {e}")
                    disconnected.append(queue)
            
            for queue in disconnected:
                self.disconnect(queue)
    
    @property
    def clients_count(self) -> int:
        """Get current number of connected clients."""
        return len(self._queues)


broadcaster = Broadcaster()