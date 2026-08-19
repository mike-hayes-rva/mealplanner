from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict


# ---------- Auth ----------

class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Tags ----------

class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str


# ---------- Ingredients ----------

class RecipeIngredientCreate(BaseModel):
    ingredient_name: str  # looked up or created on the fly
    quantity: Optional[float] = None
    unit: Optional[str] = None  # free text, e.g. "pinch", "cups"
    notes: Optional[str] = None


class RecipeIngredientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    quantity: Optional[float]
    unit: Optional[str]
    notes: Optional[str]
    ingredient_name: str

    @classmethod
    def from_orm_with_name(cls, ri):
        return cls(
            id=ri.id,
            quantity=ri.quantity,
            unit=ri.unit,
            notes=ri.notes,
            ingredient_name=ri.ingredient.name,
        )


# ---------- Steps ----------

class RecipeStepCreate(BaseModel):
    step_number: int
    instruction_text: str


class RecipeStepOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    step_number: int
    instruction_text: str


# ---------- Recipes ----------

class RecipeCreate(BaseModel):
    title: str
    description: Optional[str] = None
    prep_time_minutes: Optional[int] = None
    cook_time_minutes: Optional[int] = None
    servings: Optional[int] = None
    is_public: bool = False
    tags: list[str] = []
    ingredients: list[RecipeIngredientCreate] = []
    steps: list[RecipeStepCreate] = []


class RecipeUpdate(BaseModel):
    """All fields optional — only supplied fields are updated."""

    title: Optional[str] = None
    description: Optional[str] = None
    prep_time_minutes: Optional[int] = None
    cook_time_minutes: Optional[int] = None
    servings: Optional[int] = None
    is_public: Optional[bool] = None
    tags: Optional[list[str]] = None
    ingredients: Optional[list[RecipeIngredientCreate]] = None
    steps: Optional[list[RecipeStepCreate]] = None


class RecipeListItem(BaseModel):
    """Lightweight shape for list views — no ingredients/steps."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    image_url: Optional[str]
    prep_time_minutes: Optional[int]
    cook_time_minutes: Optional[int]
    servings: Optional[int]
    is_public: bool


class RecipeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: Optional[str]
    prep_time_minutes: Optional[int]
    cook_time_minutes: Optional[int]
    servings: Optional[int]
    image_url: Optional[str]
    is_public: bool
    created_at: datetime
    updated_at: datetime
    tags: list[TagOut]
    ingredients: list[RecipeIngredientOut]
    steps: list[RecipeStepOut]

    @classmethod
    def from_orm_full(cls, recipe):
        return cls(
            id=recipe.id,
            title=recipe.title,
            description=recipe.description,
            prep_time_minutes=recipe.prep_time_minutes,
            cook_time_minutes=recipe.cook_time_minutes,
            servings=recipe.servings,
            image_url=recipe.image_url,
            is_public=recipe.is_public,
            created_at=recipe.created_at,
            updated_at=recipe.updated_at,
            tags=[TagOut.model_validate(t) for t in recipe.tags],
            ingredients=[RecipeIngredientOut.from_orm_with_name(ri) for ri in recipe.ingredients],
            steps=[RecipeStepOut.model_validate(s) for s in recipe.steps],
        )
