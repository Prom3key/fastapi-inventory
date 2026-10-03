from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# SQLite для простоты (легко деплоить, не требует настройки БД)
DATABASE_URL = "sqlite:///./inventory.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # нужно для SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


# Зависимость для получения сессии БД (используется в роутах)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()