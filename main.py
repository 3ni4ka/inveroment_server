import asyncio
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from api.routes import auth, stock, health, material_groups, users
from config import config
from infrastructure.database.connection_pool import database_service

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Warehouse Inventory API", version="1.0.0")

# CORS middleware - разрешаем доступ из локальной сети
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.1.137:5173",  # IP сервера с клиентом
        "http://192.168.1.*",  # вся сеть (не работает, нужно указывать конкретные)
        # Или для всех (только для теста)
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Регистрируем роуты
app.include_router(health.router, prefix="", tags=["System"])
app.include_router(auth.router)
app.include_router(stock.router)
app.include_router(material_groups.router)
app.include_router(users.router)

# Добавим тестовый эндпоинт для проверки CORS
@app.options("/test-cors")
async def test_cors():
    return {"message": "CORS works!"}

class WarehouseServer:
    async def start(self):
        logger.info("🚀 Starting Warehouse Server...")
        await database_service.start()
        logger.info(f"✅ Server started on http://{config.server.host}:{config.server.port}")
        
    async def stop(self):
        logger.info("🛑 Stopping Warehouse Server...")
        await database_service.stop()

async def main():
    server = WarehouseServer()
    await server.start()
    
    config_uv = uvicorn.Config(
        app=app,
        host=config.server.host,
        port=config.server.port,
        log_level="info"
    )
    server_uv = uvicorn.Server(config_uv)
    await server_uv.serve()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")