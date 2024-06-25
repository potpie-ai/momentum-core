import logging
import re
from typing import Callable
from fastapi import Request, FastAPI, HTTPException
from fastapi import BackgroundTasks
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse
import posthog
import os
import time

logger = logging.getLogger("uvicorn.error")

event_names = {
    "/signup-post": "User Signup",
    "/webhook-post": "Automated Parse Update",
    "/parse-post": "Parse API",
    "/endpoints/list-get": "List Endpoints",
    "/endpoints/blast-get": "Blast Radius"
}


class PostHogMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, posthog_api_key: str):
        super().__init__(app)
        posthog.project_api_key = posthog_api_key
        posthog.host = os.getenv('POSTHOG_HOST', 'https://us.i.posthog.com')

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        response = await call_next(request)
        try:
            if response.status_code >= 400:
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk
                raise HTTPException(status_code=response.status_code, detail=response_body.decode("utf-8"))
        except Exception as e:
            process_time = time.time() - start_time
            error_message = self.extract_error_message(str(e))
            return self.handle_error(request, error_message, response.status_code, process_time)

        try:
            process_time = time.time() - start_time
            if hasattr(request.state, 'user'):
                user = request.state.user
                user_email = user["email"]
                user_id = user['user_id']
                event_details = f"{request.url.path}-{request.method.lower()}"
                event_type = self.get_event_type(event_details)
                if event_type:
                    background_tasks = BackgroundTasks()
                    background_tasks.add_task(
                        self.capture_event,
                        user_id=user_id,
                        user_email=user_email,
                        request=request,
                        event_type=event_type,
                        properties={
                            'path': request.url.path,
                            'method': request.method,
                            'status_code': response.status_code,
                            'process_time': process_time
                        }
                    )
                    response.background = background_tasks
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"Error during event capturing: {str(e)}")
            error_message = self.extract_error_message(str(e))
            return self.handle_error(request, error_message, response.status_code, process_time)

        return response

    def handle_error(self, request: Request, error_message, error_code: int, process_time: float) -> JSONResponse:
        background_tasks = BackgroundTasks()
        background_tasks.add_task(
            self.capture_event,
            request=request,
            user_id='unavailable',
            user_email='unavailable',
            event_type="error",
            properties={
                'path': request.url.path,
                'method': request.method,
                'error_message': error_message,
                'status_code': error_code,
                'process_time': process_time
            }
        )
        response = JSONResponse(
            status_code=error_code,
            content={"detail": error_message}
        )
        response.background = background_tasks
        return response

    # TODO Make error messages in the response uniform, and add the error message in the properties
    @staticmethod
    async def capture_event(user_email: str, event_type: str, user_id: str,
                            properties: dict, request: Request):
        if hasattr(request.state, 'additional_data') and request.state.additional_data:
            additional_data = request.state.additional_data
            logger.info(f"Sending the Event {event_type} to Posthog")
            posthog.capture(
                user_email,
                event=event_type,
                properties=additional_data
            )

    @staticmethod
    def get_event_type(url_path):
        return event_names.get(url_path)

    @staticmethod
    def extract_error_message(error_str):
        match = re.search(r'\d{3}: {\"detail\":\"(.+?)\"}', error_str)
        if match:
            return match.group(1)
        return None
