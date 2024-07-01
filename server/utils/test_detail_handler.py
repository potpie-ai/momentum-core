import datetime

from server.schemas.user_subscription_detail import UserSubscriptionDetail
from server.schemas.user_test_details import UserTestDetail


class UserTestDetailsManager:
    def __init__(self):
        pass

    def send_user_test_details(self, project_id: str, user_id: str, number_of_tests_generated: int, repo_name: str, branch_name: str):
        return

    def get_test_count_last_month(self, user_id: str) -> int:
        return 0

    def is_pro_plan(self, user_id):
        return False