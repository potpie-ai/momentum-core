import json
from datetime import datetime

from fastapi import Request
from fastapi.responses import JSONResponse, Response

from server.handler.auth_handler import auth_handler
from server.handler.user_handler import user_handler
from server.models.login_request import LoginRequest
from server.models.user import CreateUser
from server.utils.APIRouter import APIRouter
from server.utils.user_service import add_users_to_additional_data

auth_router = APIRouter()


@auth_router.post("/login")
async def login(login_request: LoginRequest):
    email, password = login_request.email, login_request.password

    try:
        res = auth_handler.login(email=email, password=password)
        id_token = res.get("idToken")
        return JSONResponse(content={"token": id_token}, status_code=200)
    except Exception as e:
        return JSONResponse(
            content={"error": f"ERROR: {str(e)}"}, status_code=400
        )


@auth_router.post("/signup")
async def signup(request: Request):
    body = json.loads(await request.body())
    uid = body["uid"]
    user = user_handler.get_user_by_uid(uid)
    if user:
        message, error = user_handler.update_last_login(uid)
        if error:
            return Response(content=message, status_code=400)
        else:
            return Response(content=json.dumps({"uid": uid}), status_code=200)
    else:
        first_login = datetime.utcnow()
        user = CreateUser(
            uid=uid,
            email=body["email"],
            display_name=body["displayName"],
            email_verified=body["emailVerified"],
            created_at=first_login,
            last_login_at=first_login,
            provider_info=body["providerData"][0],
            provider_username=body["providerUsername"]
        )
        uid, message, error = user_handler.create_user(user)
        add_users_to_additional_data(request, body)
        if error:
            return Response(content=message, status_code=400)
        return Response(content=json.dumps({"uid": uid}), status_code=201)
