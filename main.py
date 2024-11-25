from fastapi import FastAPI, Depends, HTTPException, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from itsdangerous import URLSafeTimedSerializer, BadSignature
from starlette import status

from models import FDataBase, User
from database import database
from auth import create_access_token, get_current_user, role_dependency, get_current_user_optional
import os
from dotenv import load_dotenv
from datetime import timedelta


load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")

if SECRET_KEY is None:
    raise ValueError("SECRET_KEY environment variable not set")

IS_PRODUCTION = os.getenv("IS_PRODUCTION", "False") == "True"

csrf_serializer = URLSafeTimedSerializer(SECRET_KEY)

def generate_csrf_token():
    return csrf_serializer.dumps("csrf_token")

def verify_csrf_token(token):
    try:
        csrf_serializer.loads(token, max_age=3600)
        return True
    except BadSignature:
        return False

app = FastAPI()
templates = Jinja2Templates(directory="templates")
dbase = FDataBase(database)
user_model = User(database)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "status_code": exc.status_code, "detail": exc.detail},
        status_code=exc.status_code,
    )

@app.get("/register", response_class=HTMLResponse)
async def show_register(request: Request, current_user: dict = Depends(get_current_user_optional)):
    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse("register.html", {"request": request, "user": current_user, "csrf_token": csrf_token})
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=True,
        samesite="Strict",
        secure=IS_PRODUCTION
    )
    return response

@app.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    response: Response,
    username: str = Form(..., max_length=50),
    password: str = Form(..., max_length=50),
    csrf_token: str = Form(...)
):
    role = "user"
    cookie_csrf_token = request.cookies.get("csrf_token")
    if not (csrf_token and cookie_csrf_token and csrf_token == cookie_csrf_token and verify_csrf_token(csrf_token)):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
    existing_user = await user_model.get_user_role(username)
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    await user_model.create_user(username, password, role)
    return RedirectResponse(url="/login", status_code=303)

@app.get("/login", response_class=HTMLResponse)
async def show_login(request: Request, current_user: dict = Depends(get_current_user_optional)):
    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse("login.html", {"request": request, "user": current_user, "csrf_token": csrf_token})
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=True,
        samesite="Strict",
        secure=IS_PRODUCTION
    )
    return response

@app.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...)
):
    cookie_csrf_token = request.cookies.get("csrf_token")
    if not (csrf_token and cookie_csrf_token and csrf_token == cookie_csrf_token and verify_csrf_token(csrf_token)):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
    user = await user_model.authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please check your username and password."
        )
    access_token = create_access_token({"sub": username, "role": user["role"]})
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=IS_PRODUCTION
    )
    return response

@app.post("/logout", response_class=HTMLResponse)
async def logout(request: Request, response: Response):
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="Strict"
    )
    return response

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, current_user: dict = Depends(get_current_user_optional)):
    menu = await dbase.getMenu()
    posts = await dbase.getPostsAnonce()
    return templates.TemplateResponse("index.html", {"request": request, "menu": menu, "posts": posts, "user": current_user})

@app.get("/post/{post_id}", response_class=HTMLResponse)
async def show_post(request: Request, post_id: int, current_user: dict = Depends(get_current_user_optional)):
    post = await dbase.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse("post.html", {"request": request, "post": post, "user": current_user, "csrf_token": csrf_token})
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=True,
        samesite="Strict",
        secure=IS_PRODUCTION
    )
    return response

@app.get("/add_post", response_class=HTMLResponse)
async def add_post(request: Request, current_user: dict = Depends(role_dependency(["admin", "manager", "user"]))):
    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse("addpost.html", {"request": request, "user": current_user, "csrf_token": csrf_token})
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=True,
        samesite="Strict",
        secure=IS_PRODUCTION
    )
    return response

@app.post("/add_post", response_class=HTMLResponse, name="add_post_form")
async def add_post_form(
    request: Request,
    name: str = Form(..., max_length=50),
    post: str = Form(..., max_length=1000),
    csrf_token: str = Form(...),
    current_user: dict = Depends(role_dependency(["admin", "manager", "user"]))
):
    cookie_csrf_token = request.cookies.get("csrf_token")
    if not (csrf_token and cookie_csrf_token and csrf_token == cookie_csrf_token and verify_csrf_token(csrf_token)):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
    success = await dbase.addPost(name, post, current_user["username"])
    if not success:
        raise HTTPException(status_code=500, detail="Failed to add post.")
    return RedirectResponse(url="/", status_code=303)

@app.get("/admin/tools", response_class=HTMLResponse)
async def admin_tools(request: Request, current_user: dict = Depends(role_dependency(["admin"]))):
    posts = await dbase.getPostsAnonce()
    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse("admin_tools.html", {"request": request, "user": current_user, "posts": posts, "csrf_token": csrf_token})
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=True,
        samesite="Strict",
        secure=IS_PRODUCTION
    )
    return response

@app.get("/manager/tools", response_class=HTMLResponse)
async def manager_tools(request: Request, current_user: dict = Depends(role_dependency(["manager"]))):
    posts = await dbase.getPostsAnonce()
    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse("manager_tools.html", {"request": request, "user": current_user, "posts": posts, "csrf_token": csrf_token})
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=True,
        samesite="Strict",
        secure=IS_PRODUCTION
    )
    return response

@app.post("/admin/delete_post/{post_id}", response_class=HTMLResponse)
async def delete_post_as_admin(
    request: Request,
    post_id: int,
    csrf_token: str = Form(...),
    current_user: dict = Depends(role_dependency(["admin"]))
):
    cookie_csrf_token = request.cookies.get("csrf_token")
    if not (csrf_token and cookie_csrf_token and csrf_token == cookie_csrf_token and verify_csrf_token(csrf_token)):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
    success = await dbase.delete_post(post_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete post")
    return RedirectResponse(url="/admin/tools", status_code=303)

@app.post("/manager/delete_post/{post_id}", response_class=HTMLResponse)
async def delete_post_as_manager(
    request: Request,
    post_id: int,
    csrf_token: str = Form(...),
    current_user: dict = Depends(role_dependency(["manager"]))
):
    cookie_csrf_token = request.cookies.get("csrf_token")
    if not (csrf_token and cookie_csrf_token and csrf_token == cookie_csrf_token and verify_csrf_token(csrf_token)):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
    post = await dbase.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post["owner_username"] == "admin":
        raise HTTPException(status_code=403, detail="Managers cannot delete posts created by admins")
    success = await dbase.delete_post(post_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete post")
    return RedirectResponse(url="/manager/tools", status_code=303)

@app.post("/user/delete_post/{post_id}", response_class=HTMLResponse)
async def delete_post_as_user(
    request: Request,
    post_id: int,
    csrf_token: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    cookie_csrf_token = request.cookies.get("csrf_token")
    if not (csrf_token and cookie_csrf_token and csrf_token == cookie_csrf_token and verify_csrf_token(csrf_token)):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
    post = await dbase.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    if current_user["username"] == post["owner_username"]:
        success = await dbase.delete_post(post_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete post.")
        return RedirectResponse(url="/", status_code=303)
    else:
        raise HTTPException(status_code=403, detail="Users can only delete their own posts.")

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()