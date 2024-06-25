from firebase_admin import auth
from loguru import logger


def check_auth(jwt: str):
    log_prefix = "AuthService::check_auth:"
    try:
        user = auth.verify_id_token(jwt)
        return user["user_id"]

    except Exception as e:
        logger.warning(f"{log_prefix} {str(e)}")
        raise Exception("User not authorised")
