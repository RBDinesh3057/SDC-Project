from pydantic import BaseModel
from typing import Optional

class UserSchema(BaseModel):
    user_id: str
    username: str
    age: int
    height: int
    weight: int
    goal: str
    intensity: str

    class Config:
        from_attributes = True

class WorkoutPlanSchema(BaseModel):
    id: int
    user_id: int
    original_plan: str
    updated_plan: Optional[str] = None
    nutrition_tip: Optional[str] = None

    class Config:
        from_attributes = True
