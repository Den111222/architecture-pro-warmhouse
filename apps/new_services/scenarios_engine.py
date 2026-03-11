import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from typing import Optional, List, Union
from datetime import datetime, timedelta
import uuid
import random

app = FastAPI(title="Scenarios Engine", version="1.0.0")


# ========== Модели данных ==========
class DeviceTrigger(BaseModel):
    type: str = "device"
    deviceId: str
    event: str
    value: Optional[float] = None


class ScheduleTrigger(BaseModel):
    type: str = "schedule"
    cron: str
    timezone: str = "Europe/Moscow"


class LocationTrigger(BaseModel):
    type: str = "location"
    zone: dict
    event: str


Trigger = Union[DeviceTrigger, ScheduleTrigger, LocationTrigger]


class Scenario(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    homeId: str
    trigger: Trigger
    conditions: Optional[List[dict]] = None
    actions: List[dict]
    enabled: bool = True
    createdAt: datetime
    updatedAt: Optional[datetime] = None


class Execution(BaseModel):
    id: str
    scenarioId: str
    triggeredAt: datetime
    triggerData: Optional[dict] = None
    actions: Optional[List[dict]] = None
    status: str
    completedAt: Optional[datetime] = None


# Request модели
class CreateScenarioRequest(BaseModel):
    name: str
    description: Optional[str] = None
    homeId: str
    trigger: dict
    conditions: Optional[List[dict]] = None
    actions: List[dict]
    enabled: bool = True


class UpdateScenarioRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    trigger: Optional[dict] = None
    conditions: Optional[List[dict]] = None
    actions: Optional[List[dict]] = None
    enabled: Optional[bool] = None


# ========== Зависимости ==========
async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(401, "Not authenticated")
    return {"id": str(uuid.uuid4()), "email": "user@example.com"}


# ========== Эндпоинты ==========
@app.post("/scenarios", response_model=Scenario, status_code=201)
async def create_scenario(request: CreateScenarioRequest, user: dict = Depends(get_current_user)):
    """Создать сценарий"""
    return Scenario(
        id=str(uuid.uuid4()),
        name=request.name,
        description=request.description,
        homeId=request.homeId,
        trigger=request.trigger,
        conditions=request.conditions,
        actions=request.actions,
        enabled=request.enabled,
        createdAt=datetime.now()
    )


@app.get("/scenarios", response_model=List[Scenario])
async def get_scenarios(homeId: str, enabled: Optional[bool] = None, user: dict = Depends(get_current_user)):
    """Получить список сценариев"""
    scenarios = []
    trigger_types = ["device", "schedule", "location"]

    for i in range(4):
        trigger_type = random.choice(trigger_types)
        if trigger_type == "device":
            trigger = DeviceTrigger(
                deviceId=str(uuid.uuid4()),
                event=random.choice(["turned_on", "turned_off", "temperature_above", "motion_detected"]),
                value=random.randint(18, 25) if "temperature" in random.choice(["", "temperature_above"]) else None
            )
        elif trigger_type == "schedule":
            trigger = ScheduleTrigger(
                cron=f"{random.randint(0, 59)} {random.randint(0, 23)} * * *",
                timezone="Europe/Moscow"
            )
        else:
            trigger = LocationTrigger(
                zone={"lat": 55.7558, "lng": 37.6173, "radius": 100},
                event=random.choice(["enter", "exit"])
            )

        scenarios.append(
            Scenario(
                id=str(uuid.uuid4()),
                name=f"Сценарий {i + 1}",
                description=f"Описание сценария {i + 1}",
                homeId=homeId,
                trigger=trigger,
                conditions=[
                    {"deviceId": str(uuid.uuid4()), "property": "temperature", "operator": ">", "value": 20}
                ] if random.choice([True, False]) else None,
                actions=[
                    {"deviceId": str(uuid.uuid4()), "command": "turn_on", "parameters": {}},
                    {"deviceId": str(uuid.uuid4()), "command": "set_target_temp", "parameters": {"temp": 22}}
                ],
                enabled=enabled if enabled is not None else random.choice([True, False]),
                createdAt=datetime.now() - timedelta(days=random.randint(1, 30)),
                updatedAt=datetime.now() - timedelta(days=random.randint(1, 10)) if random.choice(
                    [True, False]) else None
            )
        )
    return scenarios


@app.get("/scenarios/{scenarioId}", response_model=Scenario)
async def get_scenario(scenarioId: str, user: dict = Depends(get_current_user)):
    """Получить сценарий по ID"""
    return Scenario(
        id=scenarioId,
        name="Если температура выше 25°",
        description="Включить кондиционер",
        homeId=str(uuid.uuid4()),
        trigger=DeviceTrigger(
            deviceId=str(uuid.uuid4()),
            event="temperature_above",
            value=25
        ),
        conditions=[],
        actions=[
            {"deviceId": str(uuid.uuid4()), "command": "turn_on", "parameters": {}},
            {"deviceId": str(uuid.uuid4()), "command": "set_mode", "parameters": {"mode": "cool"}}
        ],
        enabled=True,
        createdAt=datetime.now() - timedelta(days=15),
        updatedAt=datetime.now() - timedelta(days=2)
    )


@app.put("/scenarios/{scenarioId}", response_model=Scenario)
async def update_scenario(scenarioId: str, request: UpdateScenarioRequest, user: dict = Depends(get_current_user)):
    """Обновить сценарий"""
    scenario = await get_scenario(scenarioId, user)
    if request.name:
        scenario.name = request.name
    if request.description is not None:
        scenario.description = request.description
    if request.trigger:
        scenario.trigger = request.trigger
    if request.conditions is not None:
        scenario.conditions = request.conditions
    if request.actions:
        scenario.actions = request.actions
    if request.enabled is not None:
        scenario.enabled = request.enabled
    scenario.updatedAt = datetime.now()
    return scenario


@app.delete("/scenarios/{scenarioId}", status_code=204)
async def delete_scenario(scenarioId: str, user: dict = Depends(get_current_user)):
    """Удалить сценарий"""
    return None


@app.post("/scenarios/{scenarioId}/enable", status_code=204)
async def enable_scenario(scenarioId: str, user: dict = Depends(get_current_user)):
    """Включить сценарий"""
    return None


@app.post("/scenarios/{scenarioId}/disable", status_code=204)
async def disable_scenario(scenarioId: str, user: dict = Depends(get_current_user)):
    """Отключить сценарий"""
    return None


@app.post("/scenarios/{scenarioId}/test", response_model=dict)
async def test_scenario(scenarioId: str, mockData: Optional[dict] = None, user: dict = Depends(get_current_user)):
    """Протестировать сценарий"""
    return {
        "triggered": random.choice([True, False]),
        "actionsExecuted": [
            "turn_on_light_living_room",
            "set_thermostat_22"
        ] if random.choice([True, False]) else []
    }


@app.get("/executions", response_model=List[Execution])
async def get_executions(
        scenarioId: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        limit: int = 50,
        user: dict = Depends(get_current_user)
):
    """Получить историю выполнения"""
    executions = []
    statuses = ["completed", "failed", "partial"]

    for i in range(min(limit, 10)):
        exec_id = str(uuid.uuid4())
        scenario_id = scenarioId or str(uuid.uuid4())
        triggered = datetime.now() - timedelta(hours=i * 3)
        completed = triggered + timedelta(seconds=random.randint(1, 10))

        executions.append(
            Execution(
                id=exec_id,
                scenarioId=scenario_id,
                triggeredAt=triggered,
                triggerData={"event": "motion.detected", "deviceId": str(uuid.uuid4())},
                actions=[
                    {"action": "turn_on", "deviceId": str(uuid.uuid4()), "status": "success"},
                    {"action": "start_recording", "deviceId": str(uuid.uuid4()), "status": "success"}
                ],
                status=random.choice(statuses),
                completedAt=completed if random.choice([True, False]) else None
            )
        )
    return executions


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8087)