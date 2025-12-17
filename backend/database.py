from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ------------------------------------------------------------------
# НАСТРОЙКА ПОДКЛЮЧЕНИЯ
# postgresql://пользователь:пароль@адрес:порт/имя_базы
# Если твой пароль не 1234, замени его здесь!
# ------------------------------------------------------------------
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:1234@localhost/study_exchange"

# Создаем "движок", который управляет соединением
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Создаем "фабрику сессий" (инструмент для создания запросов к базе)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс, от которого будут наследоваться все наши модели (таблицы)
Base = declarative_base()

# Функция-помощник: открывает соединение, выполняет работу и закрывает
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()