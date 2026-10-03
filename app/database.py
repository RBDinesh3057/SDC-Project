from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./fitbuddy.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Specific DB functions requested
def save_user(db, user_id: str, username: str, age: int, height: int, weight: int, goal: str, intensity: str):
    from .models import User
    user = User(user_id=user_id, username=username, age=age, height=height, weight=weight, goal=goal, intensity=intensity)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def save_plan(db, user_db_id: int, original_plan: str, nutrition_tip: str):
    from .models import WorkoutPlan
    wp = WorkoutPlan(user_id=user_db_id, original_plan=original_plan, nutrition_tip=nutrition_tip)
    db.add(wp)
    db.commit()
    db.refresh(wp)
    return wp

def update_plan(db, wp_id: int, updated_plan_text: str):
    from .models import WorkoutPlan
    wp = db.query(WorkoutPlan).filter(WorkoutPlan.id == wp_id).first()
    if wp:
        wp.updated_plan = updated_plan_text
        db.commit()
        db.refresh(wp)
    return wp

def get_user(db, user_id: str):
    from .models import User
    return db.query(User).filter(User.user_id == user_id).first()

def get_original_plan(db, wp_id: int):
    from .models import WorkoutPlan
    wp = db.query(WorkoutPlan).filter(WorkoutPlan.id == wp_id).first()
    return wp.original_plan if wp else None

def get_all_users(db):
    from .models import User
    return db.query(User).all()
