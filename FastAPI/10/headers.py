import json

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI(title="Books API")


# curl -X GET http://127.0.0.1:8000/check_headers/ -H "X-token: secret-token"
# {"User-Agent":"curl/8.13.0","X-Token":"secret-token"}
# curl -X GET http://127.0.0.1:8000/check_headers/ -H "X-token: secret"
# {"detail":"X-Token header invalid"}
# curl -X GET http://127.0.0.1:8000/check_headers/
# {"detail":[{"type":"missing","loc":["header","x-token"],"msg":"Field required","input":null}]}
@app.get("/check_headers/")
async def check_headers(
    request: Request, user_agent: str = Header(None), x_token: str = Header(...)
):
    """Перевірка заголовків."""
    print(f"Заголовки запиту: {json.dumps(dict(request.headers.items()), indent=4)}")

    if x_token != "secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")

    return {"User-Agent": user_agent, "X-Token": x_token}


# curl -X GET http://127.0.0.1:8000/check_auth/ -H "Authorization: Bearer mysecrettoken"
# {"Authorization":"success","API_key":null}
# curl -X GET http://127.0.0.1:8000/check_auth/ -H "Authorization: Bearer mysecrettok"
# {"detail":"Unauthorized."}
# curl -X GET http://127.0.0.1:8000/check_auth/ -H "Authorization: Bearer mysecrettoken" -H "X-API-key: mysecretkey"
# {"Authorization":"success","API_key":"mysecretkey"}
# curl -X GET http://127.0.0.1:8000/check_auth/ -H "Authorization: Bearer mysecrettoken" -H "X-API-key: mysecretkey" -H "Accept: text/html"
# {"Authorization":"success","API_key":"mysecretkey"}
@app.get("/check_auth/", response_model=None)
async def check_auth(
    request: Request,
    x_api_key: str = Header(default=None),
    authorization: str = Header(default=...),
    accept: str = Header(default="application/json"),
) -> HTMLResponse | JSONResponse:
    """Перевірка заголовків авторизації та типу очікуваних даних."""
    print(f"Заголовки запиту: {json.dumps(dict(request.headers.items()), indent=4)}")

    token = authorization.split()[1]
    if token != "mysecrettoken":
        raise HTTPException(401, "Unauthorized.")

    data = {"Authorization": "success", "API_key": x_api_key}

    if "text/html" in accept:
        content = f"<html><body><h1>Авторизація успішна</h1><p>API Key: {x_api_key}</p></body></html>"
        response = HTMLResponse(content=content)
    else:
        response = JSONResponse(content=data)

    print(
        f"Заголовки відповіді: {json.dumps(dict(response.headers.items()), indent=4)}"
    )
    return response
