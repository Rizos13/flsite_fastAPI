from fastapi import FastAPI, Depends, HTTPException, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from models import FDataBase, User
from database import database
from auth import create_access_token, verify_token
import os
from dotenv import load_dotenv


load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")

if SECRET_KEY is None:
    raise ValueError("SECRET_KEY environment variable not set")


app = FastAPI()
templates = Jinja2Templates(directory="templates")
dbase = FDataBase(database)
user_model = User(database)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/register", response_class=HTMLResponse)
async def show_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    response: Response,
    username: str = Form(..., max_length=50),
    password: str = Form(..., max_length=50),
    role: str = Form("user")
):
    existing_user = await user_model.get_user_role(username)
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    await user_model.create_user(username, password, role)
    return RedirectResponse(url="/login", status_code=303)


@app.get("/login", response_class=HTMLResponse)
async def show_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...)
):
    user = await user_model.authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": username, "role": user["role"]})
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response


@app.get("/logout", response_class=HTMLResponse)
async def logout(response: Response):
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response


@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    menu = await dbase.getMenu()
    posts = await dbase.getPostsAnonce()
    return templates.TemplateResponse("index.html", {"request": request, "menu": menu, "posts": posts})

@app.get("/add_post", response_class=HTMLResponse)
async def add_post(request: Request):
    return templates.TemplateResponse("addpost.html", {"request": request})

@app.post("/add_post", response_class=HTMLResponse)
async def add_post_form(
    request: Request,
    name: str = Form(..., max_length=10),
    post: str = Form(..., max_length=1000),
    payload: dict = Depends(verify_token)
):
    if payload["role"] not in ["admin", "user"]:
        raise HTTPException(status_code=403, detail="Not authorized to add post")

    success = await dbase.addPost(name, post)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to add post.")
    return RedirectResponse(url="/", status_code=303)

@app.get("/post/{post_id}", response_class=HTMLResponse)
async def show_post(request: Request, post_id: int):
    post = await dbase.getPost(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    return templates.TemplateResponse("post.html", {"request": request, "post": post})
