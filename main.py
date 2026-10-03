
from database import Base, engine, get_db
from fastapi import Depends, FastAPI, HTTPException, Path, Query
from models import (
    DeviceCreate,
    DeviceDB,
    DeviceResponse,
    DisputeCreate,
    DisputeDB,
    DisputeResponse,
)
from sqlalchemy.orm import Session

# Создаём таблицы при старте (для SQLite)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Inventory API",
    description="REST API для учёта оборудования НТЦ",
    version="1.0.0"
)


# ==================== РОУТЫ ====================

@app.get("/api/search", response_model=list[DeviceResponse], tags=["Поиск"])
def search_devices(
    q: str = Query(..., min_length=1, description="Поисковый запрос"),
    device_type: str | None = Query(None, description="Фильтр по типу устройства"),
    limit: int = Query(50, ge=1, le=100, description="Максимум результатов"),
    db: Session = Depends(get_db)  # noqa: B008
):
    """
    Универсальный поиск оборудования по system_id, serial_number, inventory_number.
    Поддерживает фильтрацию по типу устройства.
    """
    query = db.query(DeviceDB).filter(
        DeviceDB.system_id.ilike(f"%{q}%") |
        DeviceDB.serial_number.ilike(f"%{q}%") |
        DeviceDB.inventory_number.ilike(f"%{q}%")
    )

    if device_type:
        query = query.filter(DeviceDB.device_type == device_type)

    return query.limit(limit).all()


@app.get("/api/devices/{device_id}", response_model=DeviceResponse, tags=["Устройства"])
def get_device(
    device_id: int = Path(..., ge=1, description="ID устройства"),
    db: Session = Depends(get_db)  # noqa: B008
):
    """Получить устройство по ID (path-параметр)."""
    device = db.query(DeviceDB).filter(DeviceDB.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")
    return device


@app.get("/api/devices", response_model=list[DeviceResponse], tags=["Устройства"])
def list_devices(
    skip: int = Query(0, ge=0, description="Пропустить N записей"),
    limit: int = Query(50, ge=1, le=1000, description="Количество записей"),
    db: Session = Depends(get_db)  # noqa: B008
):
    """Список устройств с пагинацией."""
    return db.query(DeviceDB).offset(skip).limit(limit).all()


@app.post("/api/devices", response_model=DeviceResponse, status_code=201, tags=["Устройства"])
def create_device(device: DeviceCreate, db: Session = Depends(get_db)):  # noqa: B008
    """
    Добавить новое устройство (body-параметр).
    Демонстрация POST-запроса.
    """
    # Проверка уникальности system_id
    existing = db.query(DeviceDB).filter(DeviceDB.system_id == device.system_id).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"system_id '{device.system_id}' уже существует")

    db_device = DeviceDB(**device.model_dump())
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


@app.post("/api/disputes", response_model=DisputeResponse, status_code=201, tags=["Оспаривания"])
def create_dispute(dispute: DisputeCreate, db: Session = Depends(get_db)):  # noqa: B008
    """
    Создать оспаривание расхождения инвентаризации (body-параметр).
    Демонстрация POST-запроса с валидацией.
    """
    # Проверяем существование устройства
    device = db.query(DeviceDB).filter(DeviceDB.id == dispute.device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail=f"Устройство с id={dispute.device_id} не найдено")

    db_dispute = DisputeDB(
        device_id=dispute.device_id,
        reason=dispute.reason,
        comment=dispute.comment,
        status="pending"
    )
    db.add(db_dispute)
    db.commit()
    db.refresh(db_dispute)
    return db_dispute


@app.get("/", tags=["Info"])
def root():
    """Корневой эндпоинт — проверка работоспособности."""
    return {
        "message": "Inventory API is running",
        "docs": "/docs",
        "version": "1.0.0"
    }