from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP, Boolean, CheckConstraint
from sqlalchemy.orm import relationship
from database import Base
import datetime


# Описание таблицы пользователей
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)

    # === НОВЫЕ ПОЛЯ (из-за которых была ошибка) ===
    is_active = Column(Boolean, default=False)  # Boolean теперь импортирован!
    verification_code = Column(String, nullable=True)
    # ==============================================

    role = Column(String, default="student")
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)


# Описание таблицы материалов
class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text, nullable=True)
    file_path = Column(String)
    category_id = Column(Integer, ForeignKey("categories.id"))
    author_id = Column(Integer, ForeignKey("users.id"))
    file_type = Column(String)
    ai_summary = Column(Text, nullable=True)
    downloads_count = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)


# Описание категорий
class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    description = Column(Text, nullable=True)