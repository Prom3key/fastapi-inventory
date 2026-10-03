import pytest
from database import Base
from fastapi.testclient import TestClient
from main import app, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# ==================== Тестовая БД ====================

TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


# Переопределяем зависимость get_db для тестов
def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


# ==================== Фикстуры ====================

@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Создаём таблицы перед каждым тестом и удаляем после."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def sample_device():
    """Создаёт тестовое устройство через API."""
    response = client.post("/api/devices", json={
        "system_id": "Y1000",
        "device_type": "computer",
        "serial_number": "S36284158",
        "inventory_number": "727827063",
        "owner": "Иванов А.А.",
        "cabinet": "247"
    })
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def sample_device_2():
    """Второе устройство (монитор) для тестов фильтрации."""
    response = client.post("/api/devices", json={
        "system_id": "M4000",
        "device_type": "monitor",
        "serial_number": "M77123456",
        "inventory_number": "727827064",
        "owner": "Петров Б.Б.",
        "cabinet": "248"
    })
    assert response.status_code == 201
    return response.json()


# ==================== ТЕСТЫ ====================

def test_root():
    """Тест корневого эндпоинта."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Inventory API is running"


def test_create_device(sample_device):
    """Тест POST /api/devices — создание устройства."""
    assert sample_device["system_id"] == "Y1000"
    assert sample_device["device_type"] == "computer"
    assert "id" in sample_device


def test_create_device_duplicate(sample_device):
    """Тест 409 при дубликате system_id."""
    response = client.post("/api/devices", json={
        "system_id": "Y1000",
        "device_type": "computer",
        "serial_number": "S999",
        "inventory_number": "999"
    })
    assert response.status_code == 409


def test_create_device_validation_error():
    """Тест 422 при невалидных данных (body-параметр)."""
    response = client.post("/api/devices", json={
        "system_id": "",  # Пустая строка — нарушение min_length
        "device_type": "invalid_type",
        "serial_number": "S999",
        "inventory_number": "999"
    })
    assert response.status_code == 422


def test_get_device_by_path(sample_device):
    """Тест GET /api/devices/{device_id} — path-параметр."""
    device_id = sample_device["id"]
    response = client.get(f"/api/devices/{device_id}")
    assert response.status_code == 200
    assert response.json()["system_id"] == "Y1000"


def test_get_device_not_found():
    """Тест 404 при несуществующем ID."""
    response = client.get("/api/devices/99999")
    assert response.status_code == 404


def test_search_devices_query(sample_device, sample_device_2):
    """Тест GET /api/search — query-параметр."""
    response = client.get("/api/search?q=Y1000")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["system_id"] == "Y1000"


def test_search_devices_with_filter(sample_device, sample_device_2):
    """Тест поиска с фильтром по типу (query-параметр)."""
    response = client.get("/api/search?q=Y1000&device_type=computer")
    assert response.status_code == 200
    assert all(d["device_type"] == "computer" for d in response.json())


def test_search_empty_query():
    """Тест 422 при пустом query-параметре."""
    response = client.get("/api/search?q=")
    assert response.status_code == 422


def test_list_devices_pagination(sample_device, sample_device_2):
    """Тест пагинации GET /api/devices."""
    response = client.get("/api/devices?skip=0&limit=10")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_create_dispute(sample_device):
    """Тест POST /api/disputes — создание оспаривания (body-параметр)."""
    response = client.post("/api/disputes", json={
        "device_id": sample_device["id"],
        "reason": "Штрих-код повреждён, оборудование физически на месте",
        "comment": "Требуется переклейка этикетки"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["device_id"] == sample_device["id"]


def test_create_dispute_device_not_found():
    """Тест 404 при оспаривании несуществующего устройства."""
    response = client.post("/api/disputes", json={
        "device_id": 99999,
        "reason": "Штрих-код повреждён, оборудование физически на месте"
    })
    assert response.status_code == 404


def test_create_dispute_validation_error():
    """Тест 422 при коротком reason (body-параметр)."""
    response = client.post("/api/disputes", json={
        "device_id": 1,
        "reason": "Коротко"  # Меньше min_length=10
    })
    assert response.status_code == 422