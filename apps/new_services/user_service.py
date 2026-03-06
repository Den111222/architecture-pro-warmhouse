import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, timedelta
import uuid
import random

app = FastAPI(title="User Service", version="1.0.0")

# ========== Модели данных ==========
class User(BaseModel):
    id: str
    email: EmailStr
    fullName: str
    phone: Optional[str] = None
    status: str = "active"
    emailVerified: bool = False
    createdAt: datetime
    lastLogin: Optional[datetime] = None
    avatar: Optional[str] = None

class Invite(BaseModel):
    id: str
    email: EmailStr
    homeId: str
    homeName: str
    invitedBy: str
    invitedByName: str
    role: str
    status: str
    createdAt: datetime
    expiresAt: datetime

class Role(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    homeId: str
    permissions: List[str]
    isDefault: bool = False
    userCount: int = 0
    createdAt: datetime

class Subscription(BaseModel):
    id: str
    planId: str
    status: str
    startDate: datetime
    endDate: Optional[datetime] = None
    autoRenew: bool = True
    features: dict = {
        "maxDevices": 10,
        "maxCameras": 2,
        "recordingDays": 7
    }

# Request/Response модели
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    accessToken: str
    refreshToken: str
    expiresIn: int
    user: User

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    fullName: str
    phone: Optional[str] = None
    inviteToken: Optional[str] = None

class CreateInviteRequest(BaseModel):
    email: EmailStr
    homeId: str
    role: str
    message: Optional[str] = None

class CreateRoleRequest(BaseModel):
    name: str
    description: Optional[str] = None
    homeId: str
    permissions: List[str]

# ========== Зависимости ==========
async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(401, "Not authenticated")
    # Имитация получения пользователя из токена
    return User(
        id=str(uuid.uuid4()),
        email="user@example.com",
        fullName="Иван Петров",
        status="active",
        emailVerified=True,
        createdAt=datetime.now() - timedelta(days=30),
        lastLogin=datetime.now()
    )

# ========== Эндпоинты ==========
@app.post("/auth/register", response_model=User, status_code=201)
async def register(request: RegisterRequest):
    """Регистрация нового пользователя"""
    # Генерируем случайные данные
    return User(
        id=str(uuid.uuid4()),
        email=request.email,
        fullName=request.fullName,
        phone=request.phone,
        status="pending",
        emailVerified=False,
        createdAt=datetime.now()
    )

@app.post("/auth/confirm-email", status_code=200)
async def confirm_email(token: str):
    """Подтверждение email"""
    return {"status": "confirmed"}

@app.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Вход в систему"""
    return LoginResponse(
        accessToken="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." + str(random.randint(1000, 9999)),
        refreshToken="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." + str(random.randint(1000, 9999)),
        expiresIn=3600,
        user=User(
            id=str(uuid.uuid4()),
            email=request.email,
            fullName="Иван Петров",
            status="active",
            emailVerified=True,
            createdAt=datetime.now() - timedelta(days=30),
            lastLogin=datetime.now()
        )
    )

@app.post("/auth/refresh", response_model=dict)
async def refresh_token(refreshToken: str):
    """Обновление токена"""
    return {
        "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." + str(random.randint(1000, 9999)),
        "expiresIn": 3600
    }

@app.post("/auth/logout", status_code=204)
async def logout(user: User = Depends(get_current_user)):
    """Выход из системы"""
    return None

@app.get("/users/me", response_model=User)
async def get_current_user_info(user: User = Depends(get_current_user)):
    """Получить профиль текущего пользователя"""
    return user

@app.patch("/users/me", response_model=User)
async def update_current_user(
    fullName: Optional[str] = None,
    phone: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    """Обновить профиль"""
    if fullName:
        user.fullName = fullName
    if phone:
        user.phone = phone
    return user

@app.put("/users/me/password", status_code=204)
async def change_password(currentPassword: str, newPassword: str, user: User = Depends(get_current_user)):
    """Изменить пароль"""
    return None

@app.delete("/users/me", status_code=202)
async def delete_current_user(reason: Optional[str] = None, user: User = Depends(get_current_user)):
    """Удалить аккаунт"""
    return {"status": "deletion_scheduled"}

@app.post("/invites", response_model=Invite, status_code=201)
async def create_invite(request: CreateInviteRequest, user: User = Depends(get_current_user)):
    """Создать приглашение"""
    return Invite(
        id=str(uuid.uuid4()),
        email=request.email,
        homeId=request.homeId,
        homeName="Мой дом",
        invitedBy=user.id,
        invitedByName=user.fullName,
        role=request.role,
        status="pending",
        createdAt=datetime.now(),
        expiresAt=datetime.now() + timedelta(days=7)
    )

@app.get("/invites/received", response_model=List[Invite])
async def get_received_invites(status: Optional[str] = None, user: User = Depends(get_current_user)):
    """Получить полученные приглашения"""
    return [
        Invite(
            id=str(uuid.uuid4()),
            email=user.email,
            homeId=str(uuid.uuid4()),
            homeName="Дача",
            invitedBy=str(uuid.uuid4()),
            invitedByName="Петр Иванов",
            role="member",
            status="pending",
            createdAt=datetime.now() - timedelta(days=1),
            expiresAt=datetime.now() + timedelta(days=6)
        )
    ]

@app.post("/invites/{inviteId}/accept", response_model=dict)
async def accept_invite(inviteId: str, user: User = Depends(get_current_user)):
    """Принять приглашение"""
    return {
        "homeId": str(uuid.uuid4()),
        "role": "member"
    }

@app.post("/roles", response_model=Role, status_code=201)
async def create_role(request: CreateRoleRequest, user: User = Depends(get_current_user)):
    """Создать роль"""
    return Role(
        id=str(uuid.uuid4()),
        name=request.name,
        description=request.description,
        homeId=request.homeId,
        permissions=request.permissions,
        isDefault=False,
        userCount=0,
        createdAt=datetime.now()
    )

@app.get("/roles", response_model=List[Role])
async def get_roles(homeId: str, user: User = Depends(get_current_user)):
    """Получить роли дома"""
    return [
        Role(
            id=str(uuid.uuid4()),
            name="Администратор",
            description="Полный доступ",
            homeId=homeId,
            permissions=["view", "control", "manage", "admin"],
            isDefault=True,
            userCount=2,
            createdAt=datetime.now() - timedelta(days=30)
        ),
        Role(
            id=str(uuid.uuid4()),
            name="Родители",
            description="Управление устройствами",
            homeId=homeId,
            permissions=["view", "control"],
            isDefault=False,
            userCount=3,
            createdAt=datetime.now() - timedelta(days=20)
        )
    ]

@app.post("/users/{userId}/roles", status_code=200)
async def assign_role_to_user(userId: str, roleId: str, homeId: str, user: User = Depends(get_current_user)):
    """Назначить роль пользователю"""
    return {"status": "assigned"}

@app.get("/subscriptions/current", response_model=Subscription)
async def get_current_subscription(user: User = Depends(get_current_user)):
    """Текущая подписка"""
    return Subscription(
        id=str(uuid.uuid4()),
        planId="premium",
        status="active",
        startDate=datetime.now() - timedelta(days=30),
        endDate=datetime.now() + timedelta(days=335),
        autoRenew=True
    )

@app.get("/subscriptions/plans", response_model=List[dict])
async def get_subscription_plans():
    """Доступные тарифы"""
    return [
        {
            "id": "free",
            "name": "Бесплатный",
            "price": 0,
            "currency": "RUB",
            "period": "month",
            "features": ["5 устройств", "1 камера", "1 день хранения"],
            "maxDevices": 5,
            "maxCameras": 1,
            "recordingDays": 1
        },
        {
            "id": "premium",
            "name": "Премиум",
            "price": 499,
            "currency": "RUB",
            "period": "month",
            "features": ["20 устройств", "4 камеры", "30 дней хранения"],
            "maxDevices": 20,
            "maxCameras": 4,
            "recordingDays": 30
        }
    ]

@app.post("/subscriptions/change", response_model=Subscription)
async def change_subscription(planId: str, paymentMethodId: Optional[str] = None, user: User = Depends(get_current_user)):
    """Сменить тариф"""
    return Subscription(
        id=str(uuid.uuid4()),
        planId=planId,
        status="active",
        startDate=datetime.now(),
        endDate=datetime.now() + timedelta(days=30) if planId != "free" else None,
        autoRenew=True
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8086)