from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

posts: list[dict] = [
    {
        "id": 1,
        "title": "Title for post one",
        "author": "Malcom X",
        "description": "This is a dummy desc",
        "date": "June 15, 2026"
    },
    {
        "id": 2,
        "title": "Title for post two",
        "author": "Silverstein Will",
        "description": "This is a dummy desc",
        "date": "June 25, 2026"
    }
]

@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
def home(request: Request):
    return templates.TemplateResponse(request, "home.html", { "title": "Home", "posts": posts })

@app.get("/api/posts")
def get_posts():
    return posts