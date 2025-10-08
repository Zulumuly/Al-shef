# bot/db/models.py
from sqlalchemy import Column, Integer, String, Text
from .database import Base

# Таблица для планов питания
class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)        # Заголовок плана
    content = Column(Text, nullable=False)        # Содержимое (например, markdown с меню)


# Таблица для рецептов
class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)         # Название рецепта
    ingredients = Column(Text, nullable=False)    # Ингредиенты (можно хранить как JSON-строку)
    instructions = Column(Text, nullable=False)   # Пошаговое приготовление
