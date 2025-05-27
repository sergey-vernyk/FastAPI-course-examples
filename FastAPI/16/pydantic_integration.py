import uvicorn
from fastapi import FastAPI, HTTPException, status
from models import Hobby, UserPydantic

app = FastAPI()

users: list[UserPydantic] = []


@app.post("/users/", status_code=status.HTTP_201_CREATED, response_model=UserPydantic)
async def create_user(user_data: UserPydantic) -> UserPydantic:
    if user_data in users:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "User already exists.")

    user = UserPydantic(name=user_data.name, email=user_data.email, age=user_data.age)
    if user_data.hobbies:
        hobbies = [
            Hobby(
                name=hobby.name,
                description=hobby.description,
                difficulty=hobby.difficulty,
                started_at=hobby.started_at,
            )
            for hobby in user_data.hobbies
        ]
        user.hobbies = hobbies
    users.append(user)
    print(users)
    return user


@app.get("/users/{email}", status_code=status.HTTP_200_OK, response_model=UserPydantic)
async def get_user(email: str):
    if email not in [data.email for data in users]:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found.")

    db_user = [data for data in users if data.email == email][0]
    if db_user:
        return UserPydantic(name=db_user.name, email=email, age=db_user.age)


if __name__ == "__main__":
    uvicorn.run("pydantic_integration:app", port=8000, reload=True)
