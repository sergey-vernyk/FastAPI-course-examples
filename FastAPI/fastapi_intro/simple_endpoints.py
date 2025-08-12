from fastapi import FastAPI, Header, Query, Request

app = FastAPI()


@app.get("/greet/")
def read_greeting1(name: str = Query(None, description="Введіть ваше ім'я")):
    if name is not None:
        return {"message": f"Вітаємо, {name}"}
    return {"message": "Вітаємо!"}


@app.get("/greet/{name}")
def read_greeting2(name: str):
    return {"message": f"Вітаємо, {name}!"}


@app.get("/get_headers/accept")
async def get_headers_accept(accept: str = Header()):
    return {"message": accept}


@app.get("/get_headers/all")
async def get_headers_all(request: Request):
    return {"message": request.headers}


# inside main.py

user_list = ["Jerry", "Joey", "Phil"]


# In FastAPI, any parameter passed to a route handler, like search_for_user,
# and is not provided in the path as a path param is treated as a query parameter.
@app.get("/search")
async def search_for_user(username: str):
    if username in user_list:
        return {"message": f"details for user {username}"}

    return {"message": "User Not Found"}


# http://127.0.0.1:8000/user/?name=John
