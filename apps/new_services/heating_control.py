import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta
import uuid
import random

app = FastAPI(title="Heating Control", version="1.0.0")

# ========== Модели данных ==========
class Thermostat(BaseModel):
    deviceId: str
    currentTemp: float
    targetTemp: float
    mode: str
    humidity: int
    battery: int
    lastUpdated: datetime

class TemperatureReading(BaseModel):
    deviceId: str
    temperature: float
    humidity: int
    battery: int
    timestamp: datetime

class HeatingSchedule(BaseModel):
    id: str
    deviceId: str
    name: Optional[str] = None
    daysOfWeek: List[str]
    time: str
    targetTemp: float
    enabled: bool = True

# Request модели
class SetTargetRequest(BaseModel):
    targetTemp: float = Field(..., ge=5, le=35)

class SetModeRequest(BaseModel):
    mode: str = Field(..., pattern="^(heat|cool|auto|off)$")

class CreateScheduleRequest(BaseModel):
    deviceId: str
    name: Optional[str] = None
    daysOfWeek: List[str]
    time: str = Field(..., pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    targetTemp: float

# ========== Зависимости ==========
async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(401, "Not authenticated")
    return {"id": str(uuid.uuid4()), "email": "user@example.com"}

# ========== Эндпоинты ==========
@app.get("/thermostats/{deviceId}", response_model=Thermostat)
async def get_thermostat(deviceId: str, user: dict = Depends(get_current_user)):
    """Получить состояние термостата"""
    return Thermostat(
        deviceId=deviceId,
        currentTemp=round(random.uniform(18.0, 25.0), 1),
        targetTemp=round(random.uniform(18.0, 25.0), 1),
        mode=random.choice(["heat", "cool", "auto", "off"]),
        humidity=random.randint(30, 70),
        battery=random.randint(10, 100),
        lastUpdated=datetime.now() - timedelta(minutes=random.randint(1, 10))
    )

@app.post("/thermostats/{deviceId}/target", status_code=202)
async def set_target_temperature(deviceId: str, request: SetTargetRequest, user: dict = Depends(get_current_user)):
    """Установить целевую температуру"""
    return {"status": "accepted", "commandId": str(uuid.uuid4())}

@app.put("/thermostats/{deviceId}/mode", status_code=202)
async def set_mode(deviceId: str, request: SetModeRequest, user: dict = Depends(get_current_user)):
    """Изменить режим работы"""
    return {"status": "accepted", "commandId": str(uuid.uuid4())}

@app.get("/thermostats/{deviceId}/history", response_model=List[TemperatureReading])
async def get_temperature_history(
    deviceId: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = 100,
    user: dict = Depends(get_current_user)
):
    """Получить историю показаний"""
    readings = []
    for i in range(min(limit, 24)):
        readings.append(
            TemperatureReading(
                deviceId=deviceId,
                temperature=round(random.uniform(18.0, 25.0), 1),
                humidity=random.randint(30, 70),
                battery=random.randint(80, 100),
                timestamp=datetime.now() - timedelta(hours=i)
            )
        )
    return readings

@app.post("/schedules", response_model=HeatingSchedule, status_code=201)
async def create_schedule(request: CreateScheduleRequest, user: dict = Depends(get_current_user)):
    """Создать расписание"""
    return HeatingSchedule(
        id=str(uuid.uuid4()),
        deviceId=request.deviceId,
        name=request.name or f"Schedule {request.time}",
        daysOfWeek=request.daysOfWeek,
        time=request.time,
        targetTemp=request.targetTemp,
        enabled=True
    )

@app.get("/schedules/{scheduleId}", response_model=HeatingSchedule)
async def get_schedule(scheduleId: str, user: dict = Depends(get_current_user)):
    """Получить расписание"""
    return HeatingSchedule(
        id=scheduleId,
        deviceId=str(uuid.uuid4()),
        name="Утро будних дней",
        daysOfWeek=["mon", "tue", "wed", "thu", "fri"],
        time="07:00",
        targetTemp=22.5,
        enabled=True
    )

@app.delete("/schedules/{scheduleId}", status_code=204)
async def delete_schedule(scheduleId: str, user: dict = Depends(get_current_user)):
    """Удалить расписание"""
    return None

@app.get("/thermostats/{deviceId}/schedules", response_model=List[HeatingSchedule])
async def get_device_schedules(deviceId: str, user: dict = Depends(get_current_user)):
    """Получить расписания устройства"""
    return [
        HeatingSchedule(
            id=str(uuid.uuid4()),
            deviceId=deviceId,
            name="Утро",
            daysOfWeek=["mon", "tue", "wed", "thu", "fri"],
            time="07:00",
            targetTemp=22.5,
            enabled=True
        ),
        HeatingSchedule(
            id=str(uuid.uuid4()),
            deviceId=deviceId,
            name="Вечер",
            daysOfWeek=["mon", "tue", "wed", "thu", "fri"],
            time="21:00",
            targetTemp=19.0,
            enabled=True
        ),
        HeatingSchedule(
            id=str(uuid.uuid4()),
            deviceId=deviceId,
            name="Выходные",
            daysOfWeek=["sat", "sun"],
            time="09:00",
            targetTemp=21.0,
            enabled=True
        )
    ]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8082)