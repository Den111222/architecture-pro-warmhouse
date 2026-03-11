import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta

import uuid
import random

app = FastAPI(title="Device Registry", version="1.0.0")

# ========== Модели данных ==========
class Home(BaseModel):
    id: str
    name: str
    address: Optional[str] = None
    timezone: str = "Europe/Moscow"
    ownerId: str
    createdAt: datetime

class DeviceModel(BaseModel):
    id: str
    vendor: str
    model: str
    type: str
    protocol: str
    capabilities: List[str]
    supportedCommands: List[str]

class Device(BaseModel):
    id: str
    homeId: str
    modelId: str
    name: Optional[str] = None
    serialNumber: str
    status: str = "inactive"
    firmwareVersion: Optional[str] = None
    lastSeenAt: Optional[datetime] = None
    settings: dict = {}
    createdAt: datetime

# Request модели
class CreateHomeRequest(BaseModel):
    name: str
    address: Optional[str] = None
    timezone: str = "Europe/Moscow"

class RegisterDeviceRequest(BaseModel):
    serialNumber: str
    modelId: str
    homeId: str
    name: Optional[str] = None

# ========== Зависимости ==========
async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(401, "Not authenticated")
    return {"id": str(uuid.uuid4()), "email": "user@example.com"}

# ========== Эндпоинты ==========
@app.post("/homes", response_model=Home, status_code=201)
async def create_home(request: CreateHomeRequest, user: dict = Depends(get_current_user)):
    """Создать дом"""
    return Home(
        id=str(uuid.uuid4()),
        name=request.name,
        address=request.address,
        timezone=request.timezone,
        ownerId=user["id"],
        createdAt=datetime.now()
    )

@app.get("/homes/{homeId}", response_model=Home)
async def get_home(homeId: str, user: dict = Depends(get_current_user)):
    """Получить информацию о доме"""
    return Home(
        id=homeId,
        name="Мой дом",
        address="ул. Ленина, д. 1",
        ownerId=user["id"],
        createdAt=datetime.now() - timedelta(days=30)
    )

@app.get("/homes/{homeId}/devices", response_model=List[Device])
async def get_home_devices(homeId: str, type: Optional[str] = None, user: dict = Depends(get_current_user)):
    """Получить устройства в доме"""
    devices = []
    for i in range(3):
        device_types = ["thermostat", "light", "lock", "camera"]
        device_type = type or random.choice(device_types)
        devices.append(
            Device(
                id=str(uuid.uuid4()),
                homeId=homeId,
                modelId=str(uuid.uuid4()),
                name=f"Устройство {i+1}",
                serialNumber=f"SN{random.randint(100000, 999999)}",
                status=random.choice(["active", "inactive", "offline"]),
                firmwareVersion=f"{random.randint(1,3)}.{random.randint(0,9)}.{random.randint(0,9)}",
                lastSeenAt=datetime.now() - timedelta(minutes=random.randint(1, 60)),
                settings={"mode": "auto"} if device_type == "thermostat" else {},
                createdAt=datetime.now() - timedelta(days=random.randint(1, 30))
            )
        )
    return devices

@app.get("/homes/{homeId}/users", response_model=List[dict])
async def get_home_users(homeId: str, user: dict = Depends(get_current_user)):
    """Получить пользователей дома"""
    return [
        {
            "userId": str(uuid.uuid4()),
            "email": "owner@example.com",
            "fullName": "Иван Петров",
            "role": "admin",
            "joinedAt": datetime.now() - timedelta(days=30)
        },
        {
            "userId": str(uuid.uuid4()),
            "email": "member@example.com",
            "fullName": "Мария Иванова",
            "role": "member",
            "joinedAt": datetime.now() - timedelta(days=15)
        }
    ]

@app.post("/devices", response_model=Device, status_code=201)
async def register_device(request: RegisterDeviceRequest, user: dict = Depends(get_current_user)):
    """Зарегистрировать устройство"""
    return Device(
        id=str(uuid.uuid4()),
        homeId=request.homeId,
        modelId=request.modelId,
        name=request.name or f"Device {request.serialNumber[-4:]}",
        serialNumber=request.serialNumber,
        status="inactive",
        firmwareVersion="1.0.0",
        createdAt=datetime.now()
    )

@app.get("/devices/{deviceId}", response_model=Device)
async def get_device(deviceId: str, user: dict = Depends(get_current_user)):
    """Получить информацию об устройстве"""
    return Device(
        id=deviceId,
        homeId=str(uuid.uuid4()),
        modelId=str(uuid.uuid4()),
        name="Термостат в спальне",
        serialNumber=f"SN{random.randint(100000, 999999)}",
        status="active",
        firmwareVersion="2.1.0",
        lastSeenAt=datetime.now() - timedelta(minutes=5),
        settings={"target_temp": 22.5, "mode": "auto"},
        createdAt=datetime.now() - timedelta(days=60)
    )

@app.patch("/devices/{deviceId}", response_model=Device)
async def update_device(deviceId: str, name: Optional[str] = None, settings: Optional[dict] = None, user: dict = Depends(get_current_user)):
    """Обновить настройки устройства"""
    device = await get_device(deviceId, user)
    if name:
        device.name = name
    if settings:
        device.settings.update(settings)
    return device

@app.delete("/devices/{deviceId}", status_code=204)
async def delete_device(deviceId: str, user: dict = Depends(get_current_user)):
    """Удалить устройство"""
    return None

@app.get("/models", response_model=List[DeviceModel])
async def get_device_models(type: Optional[str] = None):
    """Получить список моделей"""
    models = []
    vendors = ["Xiaomi", "Philips", "Aqara", "Sonoff"]
    for i in range(5):
        model_type = type or random.choice(["thermostat", "light", "lock", "camera", "sensor"])
        models.append(
            DeviceModel(
                id=str(uuid.uuid4()),
                vendor=random.choice(vendors),
                model=f"Model-{random.randint(100, 999)}",
                type=model_type,
                protocol=random.choice(["mqtt", "zigbee", "wifi"]),
                capabilities={
                    "thermostat": ["temperature", "humidity", "battery"],
                    "light": ["power", "brightness", "color"],
                    "lock": ["lock", "unlock", "battery"],
                    "camera": ["video", "motion", "audio"],
                    "sensor": ["motion", "temperature", "humidity"]
                }.get(model_type, []),
                supportedCommands={
                    "thermostat": ["on", "off", "set_temp", "set_mode"],
                    "light": ["on", "off", "set_brightness", "set_color"],
                    "lock": ["lock", "unlock"],
                    "camera": ["start_record", "stop_record"],
                    "sensor": []
                }.get(model_type, [])
            )
        )
    return models

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)