from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .database import get_db, save_plan, update_plan, get_original_plan
from .models import User, WorkoutPlan, Credential
from .auth import (
    hash_password, verify_password, get_current_user, set_login_cookie, COOKIE
)

from .gemini_generator import generate_plan_and_tip
from .updated_plan import get_updated_plan

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def go(url: str):
    return RedirectResponse(url, status_code=303)


def render(request, name, user, **ctx):
    return templates.TemplateResponse(name, {"request": request, "user": user, **ctx})


def result_ctx(user, wp, plan):
    return dict(
        username=user.username, user_id=user.user_id, age=user.age, height=user.height,
        weight=user.weight, goal=user.goal, intensity=user.intensity,
        plan=plan, tip=wp.nutrition_tip, wp_id=wp.id,
    )


# ---------- public pages ----------
@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        return go("/dashboard")
    return render(request, "index.html", None)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, db: Session = Depends(get_db)):
    if get_current_user(request, db):
        return go("/dashboard")
    return render(request, "login.html", None, mode="login", error=None)


@router.post("/login", response_class=HTMLResponse)
async def login(request: Request, user_id: str = Form(...), password: str = Form(...),
                db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id.strip().lower()).first()
    cred = db.query(Credential).filter(Credential.user_id == user.id).first() if user else None
    if not cred or not verify_password(password, cred.password_hash):
        return render(request, "login.html", None, mode="login", error="Wrong user ID or password.")
    resp = go("/dashboard")
    set_login_cookie(resp, user.id)
    return resp


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, db: Session = Depends(get_db)):
    if get_current_user(request, db):
        return go("/dashboard")
    return render(request, "login.html", None, mode="register", error=None)


@router.post("/register", response_class=HTMLResponse)
async def register(request: Request, username: str = Form(...), user_id: str = Form(...),
                   password: str = Form(...), db: Session = Depends(get_db)):
    uid = user_id.strip().lower()
    error = None
    if len(password) < 6:
        error = "Password must be at least 6 characters."
    elif db.query(User).filter(User.user_id == uid).first():
        error = "That user ID is already taken."
    if error:
        return render(request, "login.html", None, mode="register", error=error)
    user = User(user_id=uid, username=username.strip())
    db.add(user)
    db.commit()
    db.refresh(user)
    db.add(Credential(user_id=user.id, password_hash=hash_password(password)))
    db.commit()
    resp = go("/dashboard")
    set_login_cookie(resp, user.id)
    return resp


@router.post("/logout")
async def logout():
    resp = go("/")
    resp.delete_cookie(COOKIE)
    return resp


# ---------- per-user pages ----------
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return go("/login")
    return render(request, "dashboard.html", user)


@router.get("/new", response_class=HTMLResponse)
async def new_plan(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return go("/login")
    return render(request, "new_plan.html", user)


@router.post("/generate-workout", response_class=HTMLResponse)
async def create_workout(
    request: Request,
    age: int = Form(...),
    height: int = Form(...),
    weight: int = Form(...),
    goal: str = Form(...),
    intensity: str = Form(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        return go("/login")

    generated_data = generate_plan_and_tip(age, weight, goal, intensity)
    plan = generated_data.get("workout_plan", "Error generating plan.")
    tip = generated_data.get("nutrition_tip", "Error generating tip.")

    user.age, user.height, user.weight = age, height, weight
    user.goal, user.intensity = goal, intensity
    db.commit()
    db.refresh(user)

    wp = save_plan(db, user.id, plan, tip)
    return render(request, "result.html", user, **result_ctx(user, wp, plan))


@router.get("/plan/{wp_id}", response_class=HTMLResponse)
async def view_plan(wp_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return go("/login")
    wp = db.query(WorkoutPlan).filter(WorkoutPlan.id == wp_id, WorkoutPlan.user_id == user.id).first()
    if not wp:
        return HTMLResponse("Plan not found.", status_code=404)
    return render(request, "result.html", user, **result_ctx(user, wp, wp.updated_plan or wp.original_plan))


@router.post("/submit-feedback", response_class=HTMLResponse)
async def submit_feedback(
    request: Request,
    wp_id: int = Form(...),
    feedback: str = Form(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        return go("/login")

    # Only the owner of a plan may modify it
    wp = db.query(WorkoutPlan).filter(WorkoutPlan.id == wp_id, WorkoutPlan.user_id == user.id).first()
    original_plan = get_original_plan(db, wp_id) if wp else None

    if wp and original_plan:
        updated_plan_text = get_updated_plan(original_plan, feedback)
        update_plan(db, wp_id, updated_plan_text)
        return render(request, "result.html", user, **result_ctx(user, wp, updated_plan_text))

    return HTMLResponse("Error: Workout plan not found.", status_code=404)


# The old global admin table exposed every user's data; it is replaced by /dashboard.
@router.get("/view-all-users")
async def view_all_users():
    return go("/dashboard")
