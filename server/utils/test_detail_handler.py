import datetime

from server.schema.user_subscription_detail import UserSubscriptionDetail
from server.schema.user_test_details import UserTestDetail


class UserTestDetailsManager:
    def __init__(self):
        pass

    def send_user_test_details(self, project_id: str, user_id: str, number_of_tests_generated: int, repo_name: str, branch_name: str):
        try:
            user_test_detail = UserTestDetail(
                project_id=project_id,
                user_id=user_id,
                number_of_tests_generated=number_of_tests_generated,
                date_of_generation=datetime.datetime.utcnow(),
                repo_name=repo_name,
                branch_name=branch_name
            )
            user_test_detail.save()
            print("Data successfully added to MongoDB.")
        except Exception as e:
            print(f"An error occurred: {e}")

    def get_test_count_last_month(self, user_id: str) -> int:
        try:
            one_month_ago = datetime.datetime.utcnow() - datetime.timedelta(days=30)
            docs = UserTestDetail.objects(user_id=user_id, date_of_generation__gte=one_month_ago)
            total_tests = sum(doc.number_of_tests_generated for doc in docs)
            return total_tests
        except Exception as e:
            print(f"An error occurred: {e}")
            return 0

    def is_pro_plan(self, user_id):
        return False
            
