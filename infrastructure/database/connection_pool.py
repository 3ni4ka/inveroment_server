import aiomysql
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, List
import logging
from config import config

logger = logging.getLogger(__name__)

class DatabaseService:
    """Сервис для работы с БД с пулом соединений"""
    
    def __init__(self):
        self.pool: Optional[aiomysql.Pool] = None
        self.is_running = False
        
    async def start(self):
        """Инициализация пула соединений"""
        try:
            self.pool = await aiomysql.create_pool(
                host=config.db.host,
                port=config.db.port,
                user=config.db.user,
                password=config.db.password,
                db=config.db.database,
                minsize=3,
                maxsize=config.db.pool_size,
                pool_recycle=config.db.pool_recycle,
                # Keep autocommit enabled for normal CRUD operations.
                # Explicit multi-step transactions are handled in transaction().
                autocommit=True,
                charset='utf8mb4'
            )
            self.is_running = True
            logger.info(f"✅ Database pool created. Size: {config.db.pool_size}")
            
            # Проверяем соединение
            async with self.get_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT 1")
                    
            logger.info("✅ Database connection verified")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize database pool: {e}")
            raise
            
    async def stop(self):
        """Закрытие пула соединений"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            logger.info("✅ Database pool closed")
        self.is_running = False
        
    @asynccontextmanager
    async def get_connection(self):
        """Получение соединения из пула"""
        if not self.pool:
            raise Exception("Database pool not initialized")
            
        async with self.pool.acquire() as conn:
            yield conn
            
    @asynccontextmanager
    async def transaction(self):
        """Транзакция с автоматическим commit/rollback"""
        async with self.get_connection() as conn:
            try:
                await conn.begin()
                yield conn
                await conn.commit()
            except Exception as e:
                await conn.rollback()
                logger.error(f"Transaction rolled back: {e}")
                raise
                
    async def execute(self, query: str, params: tuple = None) -> int:
        """Выполнение запроса (INSERT, UPDATE, DELETE)"""
        async with self.get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)
                await conn.commit()
                return cur.rowcount
                
    async def fetch_one(self, query: str, params: tuple = None) -> Optional[Dict]:
        """Получение одной записи"""
        async with self.get_connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, params)
                result = await cur.fetchone()
                logger.info(f"fetch_one result: {result}")
                return result
                
    async def fetch_all(self, query: str, params: tuple = None) -> List[Dict]:
        """Получение всех записей"""
        async with self.get_connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, params)
                return await cur.fetchall()
                
    async def call_procedure(self, proc_name: str, *args) -> List[Dict]:
        """Вызов хранимой процедуры"""
        async with self.get_connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.callproc(proc_name, args)
                results = []
                while True:
                    result = await cur.fetchone()
                    if result is None:
                        break
                    results.append(result)
                return results

# Создаём глобальный экземпляр
database_service = DatabaseService()