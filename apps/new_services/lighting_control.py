import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta
import uuid
import random
import re

app = FastAPI(title="Lighting Control", version="1.0.0")

# ========== Модели данных ==========
class Light(BaseModel):
    deviceId: str
    power: bool
    brightness: int = Field(100, ge=0, le=100)
    colorHex: Optional[str] = None
    colorTemperature: Optional[int] = Field(None, ge=2000, le=6500)
    online: bool
    lastUpdated: datetime

class LightGroup(BaseModel):
    id: str
    name: str
    deviceIds: List[str]
    createdAt: datetime

class LightingScene(BaseModel):
    id: str
    name: str
    actions: List[dict]
    createdAt: datetime

# Request модели
class SetPowerRequest(BaseModel):
    state: str = Field(..., pattern="^(on|off)$")

class SetBrightnessRequest(BaseModel):
    brightness: int = Field(..., ge=0, le=100)

class SetColorRequest(BaseModel):
    hex: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    temperature: Optional[int] = Field(None, ge=2000, le=6500)

class CreateGroupRequest(BaseModel):
    name: str
    deviceIds: List[str]

class CreateSceneRequest(BaseModel):
    name: str
    actions: List[dict]

# ========== Зависимости ==========
async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(401, "Not authenticated")
    return {"id": str(uuid.uuid4()), "email": "user@example.com"}

# ========== Эндпоинты ==========
@app.get("/lights/{deviceId}", response_model=Light)
async def get_light(deviceId: str, user: dict = Depends(get_current_user)):
    """Получить состояние лампы"""
    return Light(
        deviceId=deviceId,
        power=random.choice([True, False]),
        brightness=random.randint(0, 100),
        colorHex=f"#{random.randint(0, 0xFFFFFF):06x}" if random.choice([True, False]) else None,
        colorTemperature=random.randint(2700, 5000) if random.choice([True, False]) else None,
        online=random.choice([True, False]),
        lastUpdated=datetime.now() - timedelta(minutes=random.randint(1, 10))
    )

@app.post("/lights/{deviceId}/power", status_code=202)
async def set_light_power(deviceId: str, request: SetPowerRequest, user: dict = Depends(get_current_user)):
    """Включить/выключить лампу"""
    return {"status": "accepted", "commandId": str(uuid.uuid4())}

@app.post("/lights/{deviceId}/brightness", status_code=202)
async def set_light_brightness(deviceId: str, request: SetBrightnessRequest, user: dict = Depends(get_current_user)):
    """Установить яркость"""
    return {"status": "accepted", "commandId": str(uuid.uuid4())}

@app.post("/lights/{deviceId}/color", status_code=202)
async def set_light_color(deviceId: str, request: SetColorRequest, user: dict = Depends(get_current_user)):
    """Установить цвет"""
    return {"status": "accepted", "commandId": str(uuid.uuid4())}

@app.post("/groups", response_model=LightGroup, status_code=201)
async def create_group(request: CreateGroupRequest, user: dict = Depends(get_current_user)):
    """Создать группу ламп"""
    return LightGroup(
        id=str(uuid.uuid4()),
        name=request.name,
        deviceIds=request.deviceIds,
        createdAt=datetime.now()
    )

@app.get("/groups", response_model=List[LightGroup])
async def get_groups(homeId: str, user: dict = Depends(get_current_user)):
    """Получить все группы"""
    return [
        LightGroup(
            id=str(uuid.uuid4()),
            name="Гостиная",
            deviceIds=[str(uuid.uuid4()) for _ in range(3)],
            createdAt=datetime.now() - timedelta(days=30)
        ),
        LightGroup(
            id=str(uuid.uuid4()),
            name="Спальня",
            deviceIds=[str(uuid.uuid4()) for _ in range(2)],
            createdAt=datetime.now() - timedelta(days=25)
        ),
        LightGroup(
            id=str(uuid.uuid4()),
            name="Кухня",
            deviceIds=[str(uuid.uuid4()) for _ in range(4)],
            createdAt=datetime.now() - timedelta(days=20)
        )
    ]

@app.get("/groups/{groupId}", response_model=LightGroup)
async def get_group(groupId: str, user: dict = Depends(get_current_user)):
    """Получить информацию о группе"""
    return LightGroup(
        id=groupId,
        name="Гостиная",
        deviceIds=[str(uuid.uuid4()) for _ in range(3)],
        createdAt=datetime.now() - timedelta(days=30)
    )

@app.post("/groups/{groupId}/power", status_code=202)
async def set_group_power(groupId: str, request: SetPowerRequest, user: dict = Depends(get_current_user)):
    """Управление группой"""
    return {"status": "accepted", "commandId": str(uuid.uuid4())}

@app.post("/scenes", response_model=LightingScene, status_code=201)
async def create_scene(request: CreateSceneRequest, user: dict = Depends(get_current_user)):
    """Создать сцену"""
    return LightingScene(
        id=str(uuid.uuid4()),
        name=request.name,
        actions=request.actions,
        createdAt=datetime.now()
    )

@app.get("/scenes", response_model=List[LightingScene])
async def get_scenes(homeId: str, user: dict = Depends(get_current_user)):
    """Получить все сцены"""
    return [
        LightingScene(
            id=str(uuid.uuid4()),
            name="Кино",
            actions=[
                {"deviceId": str(uuid.uuid4()), "power": True, "brightness": 20},
                {"deviceId": str(uuid.uuid4()), "power": False}
            ],
            createdAt=datetime.now() - timedelta(days=10)
        ),
        LightingScene(
            id=str(uuid.uuid4()),
            name="Утро",
            actions=[
                {"deviceId": str(uuid.uuid4()), "power": True, "brightness": 80},
                {"deviceId": str(uuid.uuid4()), "power": True, "brightness": 100}
            ],
            createdAt=datetime.now() - timedelta(days=15)
        )
    ]

@app.post("/scenes/{sceneId}/activate", status_code=202)
async def activate_scene(sceneId: str, user: dict = Depends(get_current_user)):
    """Активировать сцену"""
    return {"status": "accepted", "executionId": str(uuid.uuid4())}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8083)