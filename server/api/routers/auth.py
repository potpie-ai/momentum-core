import json
import os

from datetime import datetime
from dotenv import load_dotenv

from fastapi import Depends, Request
from fastapi.responses import JSONResponse, Response

from server.handler.auth_handler import auth_handler
from server.handler.user_handler import user_handler

from server.utils.APIRouter import APIRouter
from server.utils.user_service import add_users_to_additional_data
from server.utils.test_detail_handler import UserTestDetailsManager

from server.auth import check_auth

from server.models.login_request import LoginRequest
from server.models.user import CreateUser

import logging

auth_router = APIRouter()
load_dotenv(override=True)

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
    
@auth_router.get("/usage")
async def usage(user=Depends(check_auth)):
    return {"tests_generated": UserTestDetailsManager().get_test_count_last_month(user["user_id"])}


def setup_dummy_user():
    user = CreateUser(
        uid= os.getenv("defaultUsername"),
        email=os.getenv("defaultUsername") + "@momentum.sh",
        display_name="Dummy User",
        email_verified=True,
        created_at=datetime.utcnow(),
        last_login_at=datetime.utcnow(),
        provider_info={},
        provider_username="self",
    )
    uid, _ , _ = user_handler.create_user(user)
    logging.info(f"Created dummy user with uid: {uid}")