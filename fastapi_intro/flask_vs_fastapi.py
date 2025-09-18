import uvicorn
from fastapi import FastAPI
from flask import Flask, Response, jsonify

app_fa = FastAPI()
app_flask = Flask(__name__)


@app_fa.get("/")
async def read_root() -> dict[str, str]:
    return {"Hello": "World"}


@app_flask.get("/")
def root() -> dict[str, str]:
    return {"message": "hello"}


@app_flask.route("/user/<username>")
def show_user_profile(username) -> Response:
    return jsonify({"User": username})


@app_fa.get("/user/")
async def show_user_profile_fa(username: str) -> dict[str, str]:
    return {"Hello": username}


if __name__ == "__main__":
    # app_flask.run()
    uvicorn.run("example2:app_fa", reload=True)


# http://google.com/user/?name=Serhii&last_name=LastName
