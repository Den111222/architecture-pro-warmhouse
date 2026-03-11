import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta
import uuid
import random

app = FastAPI(title="Access Control", version="1.0.0")


# ========== Модели данных ==========
class Lock(BaseModel):
    deviceId: str
    state: str
    battery: Optional[int] = None
    lastAction: Optional[datetime] = None
    lastActionBy: Optional[str] = None


class Gate(BaseModel):
    deviceId: str
    state: str
    lastAction: Optional[datetime] = None
    lastActionBy: Optional[str] = None


class Permission(BaseModel):
    id: str
    userId: str
    deviceId: str
    actions: List[str]
    validFrom: Optional[datetime] = None
    validTo: Optional[datetime] = None
    createdAt: datetime
    createdBy: str


class TemporaryCode(BaseModel):
    id: str
    code: str
    phone: Optional[str] = None
    deviceId: str
    validFrom: datetime
    validTo: datetime
    uses: int = 0
    maxUses: int = 1
    status: str = "active"


class AuditEntry(BaseModel):
    id: str
    userId: Optional[str] = None
    deviceId: Optional[str] = None
    action: str
    result: str
    details: Optional[dict] = None
    ipAddress: Optional[str] = None
    timestamp: datetime


# Request модели
class CreatePermissionRequest(BaseModel):
    userId: str
    deviceId: str
    actions: List[str]
    validFrom: Optional[datetime] = None
    validTo: Optional[datetime] = None


class CreateTemporaryRequest(BaseModel):
    phone: str
    deviceId: str
    validFrom: datetime
    validTo: datetime
    maxUses: int = 1


class VerifyCodeRequest(BaseModel):
    code: str
    deviceId: str


# ========== Зависимости ==========
async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(401, "Not authenticated")
    return {"id": str(uuid.uuid4()), "email": "user@example.com"}


# ========== Эндпоинты ==========
@app.post("/locks/{deviceId}/lock", status_code=202)
async def lock_device(deviceId: str, user: dict = Depends(get_current_user)):
    """Закрыть замок"""
    return {"status": "accepted", "commandId": str(uuid.uuid4())}


@app.post("/locks/{deviceId}/unlock", status_code=202)
async def unlock_device(deviceId: str, user: dict = Depends(get_current_user)):
    """Открыть замок"""
    return {"status": "accepted", "commandId": str(uuid.uuid4())}


@app.get("/locks/{deviceId}", response_model=Lock)
async def get_lock_state(deviceId: str, user: dict = Depends(get_current_user)):
    """Получить состояние замка"""
    return Lock(
        deviceId=deviceId,
        state=random.choice(["locked", "unlocked", "jammed"]),
        battery=random.randint(10, 100),
        lastAction=datetime.now() - timedelta(minutes=random.randint(1, 60)),
        lastActionBy=user["id"] if random.choice([True, False]) else None
    )


@app.post("/gates/{deviceId}/open", status_code=202)
async def open_gate(deviceId: str, user: dict = Depends(get_current_user)):
    """Открыть ворота"""
    return {"status": "accepted", "commandId": str(uuid.uuid4())}


@app.post("/gates/{deviceId}/close", status_code=202)
async def close_gate(deviceId: str, user: dict = Depends(get_current_user)):
    """Закрыть ворота"""
    return {"status": "accepted", "commandId": str(uuid.uuid4())}


@app.post("/gates/{deviceId}/stop", status_code=202)
async def stop_gate(deviceId: str, user: dict = Depends(get_current_user)):
    """Остановить ворота"""
    return {"status": "accepted", "commandId": str(uuid.uuid4())}


@app.get("/gates/{deviceId}", response_model=Gate)
async def get_gate_state(deviceId: str, user: dict = Depends(get_current_user)):
    """Получить состояние ворот"""
    return Gate(
        deviceId=deviceId,
        state=random.choice(["open", "closed", "opening", "closing", "stopped"]),
        lastAction=datetime.now() - timedelta(minutes=random.randint(1, 60)),
        lastActionBy=user["id"] if random.choice([True, False]) else None
    )


@app.post("/permissions", response_model=Permission, status_code=201)
async def create_permission(request: CreatePermissionRequest, user: dict = Depends(get_current_user)):
    """Назначить права доступа"""
    return Permission(
        id=str(uuid.uuid4()),
        userId=request.userId,
        deviceId=request.deviceId,
        actions=request.actions,
        validFrom=request.validFrom,
        validTo=request.validTo,
        createdAt=datetime.now(),
        createdBy=user["id"]
    )


@app.get("/permissions/user/{userId}", response_model=List[Permission])
async def get_user_permissions(userId: str, user: dict = Depends(get_current_user)):
    """Получить права пользователя"""
    return [
        Permission(
            id=str(uuid.uuid4()),
            userId=userId,
            deviceId=str(uuid.uuid4()),
            actions=["lock", "unlock", "view"],
            validFrom=datetime.now() - timedelta(days=30),
            validTo=datetime.now() + timedelta(days=30),
            createdAt=datetime.now() - timedelta(days=30),
            createdBy=str(uuid.uuid4())
        ),
        Permission(
            id=str(uuid.uuid4()),
            userId=userId,
            deviceId=str(uuid.uuid4()),
            actions=["open", "close"],
            validFrom=datetime.now() - timedelta(days=15),
            validTo=None,
            createdAt=datetime.now() - timedelta(days=15),
            createdBy=str(uuid.uuid4())
        )
    ]


@app.delete("/permissions/{permissionId}", status_code=204)
async def revoke_permission(permissionId: str, user: dict = Depends(get_current_user)):
    """Отозвать права"""
    return None


@app.post("/access/temporary", response_model=TemporaryCode, status_code=201)
async def create_temporary_access(request: CreateTemporaryRequest, user: dict = Depends(get_current_user)):
    """Создать временный доступ"""
    code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    return TemporaryCode(
        id=str(uuid.uuid4()),
        code=code,
        phone=request.phone,
        deviceId=request.deviceId,
        validFrom=request.validFrom,
        validTo=request.validTo,
        maxUses=request.maxUses,
        status="active"
    )


@app.post("/access/verify-code", response_model=dict)
async def verify_code(request: VerifyCodeRequest):
    """Проверить временный код"""
    # Имитация проверки
    if request.code == "123456":
        return {
            "granted": True,
            "deviceId": request.deviceId
        }
    elif request.code == "000000":
        return {
            "granted": False,
            "reason": "expired"
        }
    else:
        return {
            "granted": random.choice([True, False]),
            "deviceId": request.deviceId,
            "reason": random.choice(["invalid", "expired", "used"]) if random.choice([True, False]) else None
        }


@app.get("/access/temporary/active", response_model=List[TemporaryCode])
async def get_active_temporary_codes(deviceId: Optional[str] = None, user: dict = Depends(get_current_user)):
    """Активные временные доступы"""
    codes = []
    for i in range(3):
        codes.append(
            TemporaryCode(
                id=str(uuid.uuid4()),
                code=f"{random.randint(100000, 999999)}",
                phone=f"+7999{random.randint(1000000, 9999999)}",
                deviceId=deviceId or str(uuid.uuid4()),
                validFrom=datetime.now(),
                validTo=datetime.now() + timedelta(days=1),
                uses=random.randint(0, 2),
                maxUses=random.choice([1, 5, 10]),
                status="active"
            )
        )
    return codes


@app.get("/audit", response_model=List[AuditEntry])
async def get_audit_log(
        deviceId: Optional[str] = None,
        userId: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        limit: int = 100,
        user: dict = Depends(get_current_user)
):
    """Получить журнал доступа"""
    entries = []
    actions = ["lock", "unlock", "open", "close", "access_denied"]
    results = ["success", "failed", "denied"]

    for i in range(min(limit, 20)):
        entries.append(
            AuditEntry(
                id=str(uuid.uuid4()),
                userId=userId or str(uuid.uuid4()),
                deviceId=deviceId or str(uuid.uuid4()),
                action=random.choice(actions),
                result=random.choice(results),
                details={"method": random.choice(["app", "keypad", "code"])},
                ip_address=f"192.168.1.{random.randint(2, 254)}",
                timestamp=datetime.now() - timedelta(hours=i)
            )
        )
    return entries


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8084)