import atexit
import os
import sentry_sdk
import logging

from dotenv import load_dotenv
from server.firebase_setup import firebase_init

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.utils.graph_db_helper import Neo4jDriverSingleton

load_dotenv(override=True)

from server.api.project_api import api_router_project
from server.api.routers.auth import auth_router, setup_dummy_user
from server.key_management.secret_manager import router as secret_router
from server.routers.webhook import router as webhook_router
from server.router import api_router as code_router

from server.utils.posthog_middleware import PostHogMiddleware
from sentry_sdk.integrations.logging import LoggingIntegration

app = FastAPI()

if os.getenv("isDevelopmentMode") == "enabled" and os.getenv("ENV") != "development":
    raise ValueError("isDevelopmentMode is enabled but ENV is not development")


if os.getenv("ENV") == "production":
    posthog_api_key = os.getenv("POSTHOG_PROJECT_KEY")
    app.add_middleware(PostHogMiddleware, posthog_api_key=posthog_api_key)
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for tracing.
        traces_sample_rate=1.0,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=1.0,
        enable_tracing=True,
        integrations=[
            LoggingIntegration(
            level=logging.WARN,        # Capture warn and above as breadcrumbs
            event_level=logging.WARN   # Send records as events
            ),
        ],
    )
else:
    logging.info("Non Production Environment, Sentry Disabled")

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def setup_project_dir():
    current_dir = os.getcwd()
    projects_dir = os.path.join(current_dir, "projects")
    os.makedirs(projects_dir, exist_ok=True)
    permission = 0o777
    os.chmod(projects_dir, permission)
    os.environ["PROJECT_PATH"] = projects_dir


def check_and_set_env_vars():
    required_env_vars = [
        "OPENAI_API_KEY",
        "OPENAI_MODEL_REASONING",
    ]
    for env_var in required_env_vars:
        if env_var not in os.environ:
            value = input(f"Enter value for {env_var}: ")
            os.environ[env_var] = value


if os.getenv("isDevelopmentMode") == "enabled":
    setup_dummy_user()
else:
    firebase_init()

    
setup_project_dir()
check_and_set_env_vars()

app.include_router(code_router)
app.include_router(api_router_project)
app.include_router(router=auth_router)
app.include_router(secret_router)
app.include_router(router=webhook_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}

# This ensures that the driver is properly closed when your application is shutting down, and system resources are released.
def shutdown():
    Neo4jDriverSingleton.close_instance()

atexit.register(shutdown)