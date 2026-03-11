import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Header, Response
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import uuid
import random

app = FastAPI(title="Surveillance", version="1.0.0")


# ========== Модели данных ==========
class Camera(BaseModel):
    deviceId: str
    name: str
    model: Optional[str] = None
    status: str
    capabilities: List[str] = []
    settings: dict = {}
    lastSeen: Optional[datetime] = None


class Recording(BaseModel):
    id: str
    cameraId: str
    startedAt: datetime
    endedAt: Optional[datetime] = None
    duration: Optional[int] = None
    size: Optional[int] = None
    thumbnail: Optional[str] = None
    hasMotion: bool = False
    url: Optional[str] = None


class SurveillanceEvent(BaseModel):
    id: str
    cameraId: str
    timestamp: datetime
    type: str
    confidence: Optional[float] = None
    snapshot: Optional[str] = None
    recordingId: Optional[str] = None


class StreamResponse(BaseModel):
    url: str
    expiresAt: datetime


# ========== Зависимости ==========
async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(401, "Not authenticated")
    return {"id": str(uuid.uuid4()), "email": "user@example.com"}


# ========== Эндпоинты ==========
@app.get("/cameras", response_model=List[Camera])
async def get_cameras(homeId: str, user: dict = Depends(get_current_user)):
    """Получить список камер"""
    cameras = []
    for i in range(3):
        cameras.append(
            Camera(
                deviceId=str(uuid.uuid4()),
                name=f"Камера {i + 1}",
                model=f"IPC-{random.randint(100, 999)}",
                status=random.choice(["online", "offline", "recording"]),
                capabilities=["motion_detection", "night_vision"] if i == 0 else ["motion_detection"],
                settings={"resolution": "1080p", "fps": 25},
                lastSeen=datetime.now() - timedelta(minutes=random.randint(1, 10)) if random.choice(
                    [True, False]) else None
            )
        )
    return cameras


@app.get("/cameras/{cameraId}", response_model=Camera)
async def get_camera(cameraId: str, user: dict = Depends(get_current_user)):
    """Получить информацию о камере"""
    return Camera(
        deviceId=cameraId,
        name="Уличная камера",
        model="IPC-4K",
        status=random.choice(["online", "offline", "recording"]),
        capabilities=["motion_detection", "night_vision", "two_way_audio"],
        settings={"resolution": "4K", "fps": 30},
        lastSeen=datetime.now() - timedelta(minutes=2)
    )


@app.get("/cameras/{cameraId}/stream", response_model=StreamResponse)
async def get_stream(cameraId: str, protocol: str = "hls", user: dict = Depends(get_current_user)):
    """Получить URL видеопотока"""
    token = f"token_{random.randint(1000, 9999)}_{uuid.uuid4()}"
    return StreamResponse(
        url=f"https://stream.teplydom.ru/cameras/{cameraId}/stream.{protocol}?token={token}",
        expiresAt=datetime.now() + timedelta(hours=1)
    )


@app.get("/cameras/{cameraId}/snapshot")
async def get_snapshot(cameraId: str, user: dict = Depends(get_current_user)):
    """Получить текущий кадр"""
    # Возвращаем заглушку изображения
    return Response(content=b"fake_image_data", media_type="image/jpeg")


@app.post("/cameras/{cameraId}/record", status_code=202)
async def start_recording(cameraId: str, duration: Optional[int] = None, user: dict = Depends(get_current_user)):
    """Начать запись"""
    return {
        "status": "accepted",
        "recordingId": str(uuid.uuid4()),
        "cameraId": cameraId
    }


@app.post("/cameras/{cameraId}/stop", status_code=202)
async def stop_recording(cameraId: str, user: dict = Depends(get_current_user)):
    """Остановить запись"""
    return {"status": "accepted"}


@app.get("/recordings", response_model=List[Recording])
async def get_recordings(
        cameraId: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        hasEvents: Optional[bool] = None,
        user: dict = Depends(get_current_user)
):
    """Получить список записей"""
    recordings = []
    for i in range(5):
        start = datetime.now() - timedelta(days=i, hours=random.randint(0, 12))
        duration = random.randint(60, 3600)
        recordings.append(
            Recording(
                id=str(uuid.uuid4()),
                cameraId=cameraId or str(uuid.uuid4()),
                startedAt=start,
                endedAt=start + timedelta(seconds=duration),
                duration=duration,
                size=duration * 1024 * 1024,
                thumbnail=f"https://storage.teplydom.ru/thumbnails/{uuid.uuid4()}.jpg",
                hasMotion=random.choice([True, False]) if hasEvents is None else hasEvents,
                url=f"https://storage.teplydom.ru/recordings/{uuid.uuid4()}.mp4"
            )
        )
    return recordings


@app.get("/recordings/{recordingId}", response_model=Recording)
async def get_recording(recordingId: str, user: dict = Depends(get_current_user)):
    """Получить информацию о записи"""
    start = datetime.now() - timedelta(days=1)
    duration = random.randint(60, 3600)
    return Recording(
        id=recordingId,
        cameraId=str(uuid.uuid4()),
        startedAt=start,
        endedAt=start + timedelta(seconds=duration),
        duration=duration,
        size=duration * 1024 * 1024,
        thumbnail=f"https://storage.teplydom.ru/thumbnails/{uuid.uuid4()}.jpg",
        hasMotion=random.choice([True, False]),
        url=f"https://storage.teplydom.ru/recordings/{recordingId}.mp4"
    )


@app.get("/recordings/{recordingId}/download")
async def download_recording(recordingId: str, user: dict = Depends(get_current_user)):
    """Скачать запись"""
    # Возвращаем заглушку видео
    return Response(content=b"fake_video_data", media_type="video/mp4")


@app.get("/events", response_model=List[SurveillanceEvent])
async def get_events(
        cameraId: Optional[str] = None,
        type: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        limit: int = 100,
        user: dict = Depends(get_current_user)
):
    """Получить события"""
    events = []
    event_types = ["motion", "person", "vehicle", "animal", "sound"]

    for i in range(min(limit, 10)):
        event_type = type or random.choice(event_types)
        events.append(
            SurveillanceEvent(
                id=str(uuid.uuid4()),
                cameraId=cameraId or str(uuid.uuid4()),
                timestamp=datetime.now() - timedelta(hours=i),
                type=event_type,
                confidence=round(random.uniform(0.7, 0.99), 2) if event_type != "sound" else None,
                snapshot=f"https://storage.teplydom.ru/snapshots/{uuid.uuid4()}.jpg" if random.choice(
                    [True, False]) else None,
                recordingId=str(uuid.uuid4()) if random.choice([True, False]) else None
            )
        )
    return events


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8085)