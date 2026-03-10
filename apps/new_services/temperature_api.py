from fastapi import FastAPI, Query, APIRouter
import random
import uvicorn
from typing import Optional

app = FastAPI(
    title="Temperature API",
    description="API для получения случайной температуры",
    version="1.0.0"
)

router = APIRouter()

# Маппинг комнат и sensorId
LOCATIONS = {
    "1": "Living Room",
    "2": "Bedroom",
    "3": "Kitchen"
}


@router.get("/temperature/{sensorId}")
async def get_temperature(
    sensorId: Optional[str],
    location: Optional[str] = Query(None, description="Название комнаты")
):
    """
    Возвращает случайную температуру для указанной комнаты или датчика

    - Если указан location, используется он
    - Если указан sensorId, определяется location по нему
    - Если ничего не указано - random
    """

    # Копируем входные параметры (чтобы не менять оригиналы)
    loc = location
    sid = sensorId

    # Если нет location, определяем по sensorId
    if not loc and sid in LOCATIONS:
        loc = LOCATIONS[sid]
    elif not loc:
        loc = "Unknown"

    # Если нет sensorId, определяем по location
    if not sid:
        for sid_key, loc_value in LOCATIONS.items():
            if loc_value.lower() == loc.lower():
                sid = sid_key
                break
        else:
            sid = "0"

    # Генерируем случайную температуру (от 18 до 26 градусов)
    temperature = round(random.uniform(18.0, 26.0), 1)

    return {
        "value": temperature,  # ← КЛЮЧЕВОЙ момент: должно быть "value"
        "status": "online",
        "lastUpdated": None,
        "sensorId": sid,
        "location": loc,
        "unit": "Celsius"
    }


@router.get("/health")
async def health():
    return {"status": "healthy"}


@router.get("/")
async def root():
    return {
        "name": "Temperature API",
        "version": "1.0.0",
        "endpoints": {
            "/temperature": "GET ?location= или ?sensorId=",
            "/health": "GET"
        }
    }

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)