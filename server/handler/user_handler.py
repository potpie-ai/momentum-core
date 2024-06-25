from loguru import logger

from server.db.session import SessionManager
from server.models.user import CreateUser
from server.schema.users import User


class UserHandler:
    def create_user(self, user_details: CreateUser):
        logger.info(
            f"Creating user with email: {user_details.email} | display_name:"
            f" {user_details.display_name}"
        )
        new_user = User(
            uid=user_details.uid,
            email=user_details.email,
            display_name=user_details.display_name,
            email_verified=user_details.email_verified,
            created_at=user_details.created_at,
            last_login_at=user_details.last_login_at,
            provider_info=user_details.provider_info,
            provider_username=user_details.provider_username,
        )
        message: str = ""
        error: bool = False
        try:
            with SessionManager() as db:
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                error = False
                message = f"User created with ID: {new_user.uid}"
                uid = new_user.uid

        except Exception as e:
            logger.error(f"Error creating user: {e}")
            message = "error creating user"
            error = True
            uid = ""

        return uid, message, error


user_handler = UserHandler()
