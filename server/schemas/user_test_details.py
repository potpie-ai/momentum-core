import datetime
from mongoengine import Document, StringField, IntField, DateTimeField
from server.utils.mongo_helper import get_mongo_connection

# Get the MongoDB connection
mongo_conn = get_mongo_connection()
class UserTestDetail(Document):
    project_id = IntField(required=True)
    user_id = StringField(required=True)
    number_of_tests_generated = IntField(required=True)
    date_of_generation = DateTimeField(default=datetime.datetime.utcnow)
    repo_name = StringField(required=True)
    branch_name = StringField(required=True)
    configuration = StringField(required=False)
    meta = {'collection': 'user_test_details'}