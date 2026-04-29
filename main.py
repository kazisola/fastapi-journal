from fastapi import FastAPI, Request, HTTPException, status
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
    return templates.TemplateResponse(
        request,
        "home.html",
        {
            "title": "Home",
            "posts": posts 
        })
@app.get("/posts/{post_id}", include_in_schema=False)
def post_page(request: Request, post_id: int):
    for post in posts:
        if post.get("id") == post_id:
            title = post["title"][:50]
            return templates.TemplateResponse(
                request,
                "post.html",
                {
                    "title": title,
                    "post": post
                }
            )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found!")

@app.get("/api/posts")
def get_posts():
    return posts

@app.get("/api/posts/{post_id}")
def get_post(post_id: int):
    for post in posts:
        if post.get("id") == post_id:
            return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found!")