from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import jwt
import os
import logging
from typing import Optional, Dict, Any
import time
from datetime import datetime, timedelta
import uuid

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация из переменных окружения
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8086")
DEVICE_SERVICE_URL = os.getenv("DEVICE_SERVICE_URL", "http://device-registry:8081")
HEATING_SERVICE_URL = os.getenv("HEATING_SERVICE_URL", "http://heating-control:8082")
LIGHTING_SERVICE_URL = os.getenv("LIGHTING_SERVICE_URL", "http://lighting-control:8083")
ACCESS_SERVICE_URL = os.getenv("ACCESS_SERVICE_URL", "http://access-control:8084")
SURVEILLANCE_SERVICE_URL = os.getenv("SURVEILLANCE_SERVICE_URL", "http://surveillance:8085")
SCENARIOS_SERVICE_URL = os.getenv("SCENARIOS_SERVICE_URL", "http://scenarios-engine:8087")
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-jwt-key-change-in-production")

app = FastAPI(
    title="Smart Home API Gateway",
    description="Единая точка входа для всех микросервисов",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# HTTP клиент с таймаутами
http_client = httpx.AsyncClient(
    timeout=30.0,
    limits=httpx.Limits(max_keepalive_connections=50, max_connections=200)
)


# ========== СЛУЖЕБНЫЕ ФУНКЦИИ ==========

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Проверка JWT токена"""
    if not token:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Получение текущего пользователя из токена"""
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


# ========== HEALTH CHECK ==========

@app.get("/health", tags=["System"])
async def health_check():
    """Проверка здоровья всех сервисов"""
    services = {
        "user": USER_SERVICE_URL,
        "device": DEVICE_SERVICE_URL,
        "heating": HEATING_SERVICE_URL,
        "lighting": LIGHTING_SERVICE_URL,
        "access": ACCESS_SERVICE_URL,
        "surveillance": SURVEILLANCE_SERVICE_URL,
        "scenarios": SCENARIOS_SERVICE_URL,
    }

    status = {}
    all_healthy = True

    for name, url in services.items():
        try:
            async with httpx.AsyncClient() as client:
                start = time.time()
                r = await client.get(f"{url}/health", timeout=2.0)
                response_time = time.time() - start
                status[name] = {
                    "status": "healthy" if r.status_code == 200 else "unhealthy",
                    "code": r.status_code,
                    "response_time": f"{response_time:.3f}s"
                }
                if r.status_code != 200:
                    all_healthy = False
        except Exception as e:
            status[name] = {
                "status": "unhealthy",
                "error": str(e)
            }
            all_healthy = False

    return {
        "gateway": {
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        },
        "services": status,
        "all_healthy": all_healthy
    }


# ========== МАРШРУТЫ К МИКРОСЕРВИСАМ ==========

# ----- USER SERVICE -----
@app.api_route("/api/v1/auth/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def auth_proxy(path: str, request: Request):
    """Прокси для аутентификации"""
    target_url = f"{USER_SERVICE_URL}/auth/{path}"
    return await proxy_request(target_url, request, public=True)


@app.api_route("/api/v1/users/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def users_proxy(path: str, request: Request, user: Dict = Depends(get_current_user)):
    """Прокси для управления пользователями"""
    target_url = f"{USER_SERVICE_URL}/users/{path}"
    return await proxy_request(target_url, request, user=user)


@app.api_route("/api/v1/roles/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def roles_proxy(path: str, request: Request, user: Dict = Depends(get_current_user)):
    """Прокси для управления ролями"""
    target_url = f"{USER_SERVICE_URL}/roles/{path}"
    return await proxy_request(target_url, request, user=user)


@app.api_route("/api/v1/invites/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def invites_proxy(path: str, request: Request, user: Dict = Depends(get_current_user)):
    """Прокси для приглашений"""
    target_url = f"{USER_SERVICE_URL}/invites/{path}"
    return await proxy_request(target_url, request, user=user)


@app.api_route("/api/v1/subscriptions/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def subscriptions_proxy(path: str, request: Request, user: Dict = Depends(get_current_user)):
    """Прокси для подписок"""
    target_url = f"{USER_SERVICE_URL}/subscriptions/{path}"
    return await proxy_request(target_url, request, user=user)


# ----- DEVICE REGISTRY -----
@app.api_route("/api/v1/homes/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def homes_proxy(path: str, request: Request, user: Dict = Depends(get_current_user)):
    """Прокси для управления домами"""
    target_url = f"{DEVICE_SERVICE_URL}/homes/{path}"
    return await proxy_request(target_url, request, user=user)


@app.api_route("/api/v1/devices/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def devices_proxy(path: str, request: Request, user: Dict = Depends(get_current_user)):
    """Прокси для управления устройствами"""
    target_url = f"{DEVICE_SERVICE_URL}/devices/{path}"
    return await proxy_request(target_url, request, user=user)


@app.api_route("/api/v1/models/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def models_proxy(path: str, request: Request, user: Dict = Depends(get_current_user)):
    """Прокси для моделей устройств"""
    target_url = f"{DEVICE_SERVICE_URL}/models/{path}"
    return await proxy_request(target_url, request, user=user)


# ----- HEATING CONTROL -----
@app.api_route("/api/v1/thermostats/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def thermostats_proxy(path: str, request: Request, user: Dict = Depends(get_current_user)):
    """Прокси для термостатов"""
    target_url = f"{HEATING_SERVICE_URL}/thermostats/{path}"
    return await proxy_request(target_url, request, user=user)


@app.api_route("/api/v1/schedules/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def heating_schedules_proxy(path: str, request: Request, user: Dict = Depends(get_current_user)):
    """Прокси для расписаний отопления"""
    target_url = f"{HEATING_SERVICE_URL}/schedules/{path}"
    return await proxy_request(target_url, request, user=user)


# ----- LIGHTING CONTROL -----
@app.api_route("/api/v1/lights/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def lights_proxy(path: str, request: Request, user: Dict = Depends(get_current_user)):
    """Прокси для ламп"""
    target_url = f"{LIGHTING_SERVICE_URL}/lights/{path}"
    return await proxy_request(target_url, request, user=user)


@app.api_route("/api/v1/groups/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def light_groups_proxy(path: str, request: Request, user: Dict = Depends(get_current_user)):
    """Прокси для групп ламп"""
    target_url = f"{LIGHTING_SERVICE_URL}/groups/{path}"
    return await proxy_request(target_url, request, user=user)


@app.api_route("/api/v1/scenes/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def light_scenes_proxy(path: str, request: Request, user: Dict = Depends(get_current_user)):
    """Прокси для сцен освещения"""
    target_url = f"{LIGHTING_SERVICE_URL}/scenes/{path}"
    return await proxy_request(target_url, request, user=user)


# ----- ACCESS CONTROL -----
@app.api_route("/api/v1/locks/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def locks_proxy(path: str, request: Request, user: Dict = Depends(get_current_user)):
    """Прокси для замков"""
    target_url = f"{ACCESS_SERVICE_URL}/locks/{path}"
    return await proxy_request(target_url, request, user=user)


@app.api_route("/api/v1/gates/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def gates_proxy(path: str, request: Request, user: Dict = Depends(get_current_user)):
    """Прокси для ворот"""
    target_url = f"{ACCESS_SERVICE_URL}/gates/{path}"
    return await proxy_request(target_url, request, user=user)


@app.api_route("/api/v1/permissions/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def permissions_proxy(path: str, request: Request, user: Dict = Depends(get_current_user)):
    """Прокси для прав доступа"""
    target_url = f"{ACCESS_SERVICE_URL}/permissions/{path}"
    return await proxy_request(target_url, request, user=user)


@app.api_route("/api/v1/access/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def access_proxy(path: str, request: Request, user: Dict = Depends(get_current_user)):
    """Прокси для временного доступа"""
    target_url = f"{ACCESS_SERVICE_URL}/access/{path}"
    return await proxy_request(target_url, request, user=user)


@app.api_route("/api/v1/audit/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def audit_proxy(path: str, request: Request, user: Dict = Depends(get_current_user)):
    """Прокси для аудита"""
    target_url = f"{ACCESS_SERVICE_URL}/audit/{path}"
    return await proxy_request(target_url, request, user=user)


# ----- SURVEILLANCE -----
@app.api_route("/api/v1/cameras/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def cameras_proxy(path: str, request: Request, user: Dict = Depends(get_current_user)):
    """Прокси для камер"""
    target_url = f"{SURVEILLANCE_SERVICE_URL}/cameras/{path}"
    return await proxy_request(target_url, request, user=user)


@app.api_route("/api/v1/recordings/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def recordings_proxy(path: str, request: Request, user: Dict = Depends(get_current_user)):
    """Прокси для записей"""
    target_url = f"{SURVEILLANCE_SERVICE_URL}/recordings/{path}"
    return await proxy_request(target_url, request, user=user)


@app.api_route("/api/v1/events/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def surveillance_events_proxy(path: str, request: Request, user: Dict = Depends(get_current_user)):
    """Прокси для событий"""
    target_url = f"{SURVEILLANCE_SERVICE_URL}/events/{path}"
    return await proxy_request(target_url, request, user=user)


# ----- SCENARIOS ENGINE -----
@app.api_route("/api/v1/scenarios/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def scenarios_proxy(path: str, request: Request, user: Dict = Depends(get_current_user)):
    """Прокси для сценариев"""
    target_url = f"{SCENARIOS_SERVICE_URL}/scenarios/{path}"
    return await proxy_request(target_url, request, user=user)


@app.api_route("/api/v1/executions/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def executions_proxy(path: str, request: Request, user: Dict = Depends(get_current_user)):
    """Прокси для выполнений"""
    target_url = f"{SCENARIOS_SERVICE_URL}/executions/{path}"
    return await proxy_request(target_url, request, user=user)


# ========== ОСНОВНАЯ ФУНКЦИЯ ПРОКСИ ==========

async def proxy_request(target_url: str, request: Request, public: bool = False, user: Dict = None):
    """Универсальная функция проксирования запросов"""

    # Логируем запрос
    logger.info(f"→ {request.method} {request.url.path} → {target_url}")

    try:
        # Подготавливаем заголовки
        headers = dict(request.headers)
        # Удаляем заголовки, которые могут вызвать проблемы
        headers.pop("host", None)
        headers.pop("content-length", None)

        # Добавляем user_id если есть
        if user and user.get("user_id"):
            headers["X-User-ID"] = str(user["user_id"])

        # Получаем тело запроса
        body = await request.body()

        # Отправляем запрос в микросервис
        resp = await http_client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body if body else None,
            params=request.query_params,
            follow_redirects=True
        )

        # Логируем ответ
        logger.info(f"← {request.method} {request.url.path} = {resp.status_code}")

        # Определяем тип контента
        content_type = resp.headers.get("content-type", "")

        # Для изображений и видео - стриминг
        if "image" in content_type or "video" in content_type or "octet-stream" in content_type:
            return StreamingResponse(
                resp.aiter_bytes(),
                status_code=resp.status_code,
                media_type=content_type,
                headers=dict(resp.headers)
            )

        # Для JSON - парсим
        try:
            return JSONResponse(
                status_code=resp.status_code,
                content=resp.json(),
                headers=dict(resp.headers)
            )
        except:
            # Для текста
            return JSONResponse(
                status_code=resp.status_code,
                content={"message": resp.text},
                headers=dict(resp.headers)
            )

    except httpx.ConnectError as e:
        logger.error(f"Connection error to {target_url}: {e}")
        return JSONResponse(
            status_code=503,
            content={"error": "Service Unavailable", "detail": str(e)}
        )
    except httpx.TimeoutException as e:
        logger.error(f"Timeout error to {target_url}: {e}")
        return JSONResponse(
            status_code=504,
            content={"error": "Gateway Timeout", "detail": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal Server Error", "detail": str(e)}
        )


# ========== ДОПОЛНИТЕЛЬНЫЕ ЭНДПОИНТЫ ==========

@app.get("/", include_in_schema=False)
async def root():
    """Корневой эндпоинт"""
    return {
        "name": "Smart Home API Gateway",
        "version": "1.0.0",
        "description": "Единая точка входа для всех микросервисов",
        "services": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "homes": "/api/v1/homes",
            "devices": "/api/v1/devices",
            "thermostats": "/api/v1/thermostats",
            "lights": "/api/v1/lights",
            "locks": "/api/v1/locks",
            "cameras": "/api/v1/cameras",
            "scenarios": "/api/v1/scenarios"
        },
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/api/v1/services", tags=["System"])
async def list_services():
    """Список доступных сервисов"""
    return {
        "services": [
            {"name": "auth", "url": USER_SERVICE_URL},
            {"name": "users", "url": USER_SERVICE_URL},
            {"name": "homes", "url": DEVICE_SERVICE_URL},
            {"name": "devices", "url": DEVICE_SERVICE_URL},
            {"name": "thermostats", "url": HEATING_SERVICE_URL},
            {"name": "lights", "url": LIGHTING_SERVICE_URL},
            {"name": "locks", "url": ACCESS_SERVICE_URL},
            {"name": "cameras", "url": SURVEILLANCE_SERVICE_URL},
            {"name": "scenarios", "url": SCENARIOS_SERVICE_URL},
        ]
    }


@app.on_event("startup")
async def startup():
    """Действия при запуске"""
    logger.info("API Gateway starting...")
    logger.info(f"User Service: {USER_SERVICE_URL}")
    logger.info(f"Device Service: {DEVICE_SERVICE_URL}")
    logger.info(f"Heating Service: {HEATING_SERVICE_URL}")
    logger.info(f"Lighting Service: {LIGHTING_SERVICE_URL}")
    logger.info(f"Access Service: {ACCESS_SERVICE_URL}")
    logger.info(f"Surveillance Service: {SURVEILLANCE_SERVICE_URL}")
    logger.info(f"Scenarios Service: {SCENARIOS_SERVICE_URL}")


@app.on_event("shutdown")
async def shutdown():
    """Закрываем соединения при остановке"""
    logger.info("Shutting down API Gateway...")
    await http_client.aclose()
    logger.info("Connections closed")