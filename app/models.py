import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    ForeignKey,
    DateTime,
    Text,
    Table,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    recipes = relationship("Recipe", back_populates="owner", cascade="all, delete-orphan")


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    prep_time_minutes = Column(Integer, nullable=True)
    cook_time_minutes = Column(Integer, nullable=True)
    servings = Column(Integer, nullable=True)
    image_url = Column(String, nullable=True)
    is_public = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    owner = relationship("User", back_populates="recipes")
    ingredients = relationship(
        "RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan"
    )
    steps = relationship(
        "RecipeStep",
        back_populates="recipe",
        cascade="all, delete-orphan",
        order_by="RecipeStep.step_number",
    )
    tags = relationship("Tag", secondary="recipe_tags", back_populates="recipes")


class Ingredient(Base):
    """Global ingredient catalog — reused across recipes."""

    __tablename__ = "ingredients"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String, unique=True, nullable=False, index=True)


class RecipeIngredient(Base):
    """Join table: how much of an ingredient a recipe uses.

    quantity is numeric and optional (e.g. "salt to taste" has no quantity).
    unit is intentionally free text (e.g. "pinch", "cups", "cloves").
    """

    __tablename__ = "recipe_ingredients"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    recipe_id = Column(UUID(as_uuid=False), ForeignKey("recipes.id"), nullable=False)
    ingredient_id = Column(UUID(as_uuid=False), ForeignKey("ingredients.id"), nullable=False)

    quantity = Column(Float, nullable=True)
    unit = Column(String, nullable=True)
    notes = Column(String, nullable=True)

    recipe = relationship("Recipe", back_populates="ingredients")
    ingredient = relationship("Ingredient")


class RecipeStep(Base):
    __tablename__ = "recipe_steps"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    recipe_id = Column(UUID(as_uuid=False), ForeignKey("recipes.id"), nullable=False)
    step_number = Column(Integer, nullable=False)
    instruction_text = Column(Text, nullable=False)

    recipe = relationship("Recipe", back_populates="steps")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String, unique=True, nullable=False, index=True)

    recipes = relationship("Recipe", secondary="recipe_tags", back_populates="tags")


recipe_tags = Table(
    "recipe_tags",
    Base.metadata,
    Column("recipe_id", UUID(as_uuid=False), ForeignKey("recipes.id"), primary_key=True),
    Column("tag_id", UUID(as_uuid=False), ForeignKey("tags.id"), primary_key=True),
)
