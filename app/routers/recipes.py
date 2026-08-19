from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session, joinedload

from app.auth import get_current_user
from app.database import get_db
from app.models import Recipe, Ingredient, RecipeIngredient, RecipeStep, Tag, User
from app.schemas import RecipeCreate, RecipeUpdate, RecipeOut, RecipeListItem
from app.storage import upload_recipe_image

router = APIRouter(prefix="/recipes", tags=["recipes"])


def _recipe_query(db: Session):
    return db.query(Recipe).options(
        joinedload(Recipe.ingredients).joinedload(RecipeIngredient.ingredient),
        joinedload(Recipe.steps),
        joinedload(Recipe.tags),
    )


def _get_owned_recipe(recipe_id: str, user: User, db: Session) -> Recipe:
    recipe = _recipe_query(db).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    if recipe.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your recipe")
    return recipe


def _get_or_create_ingredient(name: str, db: Session) -> Ingredient:
    ingredient = db.query(Ingredient).filter(Ingredient.name == name).first()
    if not ingredient:
        ingredient = Ingredient(name=name)
        db.add(ingredient)
        db.flush()  # get its id without a full commit
    return ingredient


def _get_or_create_tag(name: str, db: Session) -> Tag:
    tag = db.query(Tag).filter(Tag.name == name).first()
    if not tag:
        tag = Tag(name=name)
        db.add(tag)
        db.flush()
    return tag


@router.get("", response_model=list[RecipeListItem])
def list_recipes(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    recipes = db.query(Recipe).filter(Recipe.user_id == user.id).order_by(Recipe.created_at.desc()).all()
    return recipes


@router.post("", response_model=RecipeOut, status_code=201)
def create_recipe(
    recipe_in: RecipeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    recipe = Recipe(
        user_id=user.id,
        title=recipe_in.title,
        description=recipe_in.description,
        prep_time_minutes=recipe_in.prep_time_minutes,
        cook_time_minutes=recipe_in.cook_time_minutes,
        servings=recipe_in.servings,
        is_public=recipe_in.is_public,
    )
    db.add(recipe)
    db.flush()  # get recipe.id

    for tag_name in recipe_in.tags:
        recipe.tags.append(_get_or_create_tag(tag_name, db))

    for ri_in in recipe_in.ingredients:
        ingredient = _get_or_create_ingredient(ri_in.ingredient_name, db)
        db.add(
            RecipeIngredient(
                recipe_id=recipe.id,
                ingredient_id=ingredient.id,
                quantity=ri_in.quantity,
                unit=ri_in.unit,
                notes=ri_in.notes,
            )
        )

    for step_in in recipe_in.steps:
        db.add(
            RecipeStep(
                recipe_id=recipe.id,
                step_number=step_in.step_number,
                instruction_text=step_in.instruction_text,
            )
        )

    db.commit()

    recipe = _recipe_query(db).filter(Recipe.id == recipe.id).first()
    return RecipeOut.from_orm_full(recipe)


@router.get("/{recipe_id}", response_model=RecipeOut)
def get_recipe(recipe_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    recipe = _get_owned_recipe(recipe_id, user, db)
    return RecipeOut.from_orm_full(recipe)


@router.put("/{recipe_id}", response_model=RecipeOut)
def update_recipe(
    recipe_id: str,
    recipe_in: RecipeUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    recipe = _get_owned_recipe(recipe_id, user, db)

    simple_fields = [
        "title", "description", "prep_time_minutes",
        "cook_time_minutes", "servings", "is_public",
    ]
    for field in simple_fields:
        value = getattr(recipe_in, field)
        if value is not None:
            setattr(recipe, field, value)

    if recipe_in.tags is not None:
        recipe.tags = [_get_or_create_tag(name, db) for name in recipe_in.tags]

    if recipe_in.ingredients is not None:
        recipe.ingredients.clear()
        db.flush()
        for ri_in in recipe_in.ingredients:
            ingredient = _get_or_create_ingredient(ri_in.ingredient_name, db)
            db.add(
                RecipeIngredient(
                    recipe_id=recipe.id,
                    ingredient_id=ingredient.id,
                    quantity=ri_in.quantity,
                    unit=ri_in.unit,
                    notes=ri_in.notes,
                )
            )

    if recipe_in.steps is not None:
        recipe.steps.clear()
        db.flush()
        for step_in in recipe_in.steps:
            db.add(
                RecipeStep(
                    recipe_id=recipe.id,
                    step_number=step_in.step_number,
                    instruction_text=step_in.instruction_text,
                )
            )

    db.commit()

    recipe = _recipe_query(db).filter(Recipe.id == recipe.id).first()
    return RecipeOut.from_orm_full(recipe)


@router.delete("/{recipe_id}", status_code=204)
def delete_recipe(recipe_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    recipe = _get_owned_recipe(recipe_id, user, db)
    db.delete(recipe)
    db.commit()


@router.post("/{recipe_id}/image", response_model=RecipeOut)
def upload_image(
    recipe_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    recipe = _get_owned_recipe(recipe_id, user, db)

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    url = upload_recipe_image(file, recipe_id)
    recipe.image_url = url
    db.commit()

    recipe = _recipe_query(db).filter(Recipe.id == recipe.id).first()
    return RecipeOut.from_orm_full(recipe)
