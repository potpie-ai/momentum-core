import datetime
import os

import certifi
from mongoengine import Document, StringField, IntField, DateTimeField, connect

connect(
    'test',
    host=os.getenv("MONGO_URI", "mongodb://localhost:27017"),
    tlsCAFile= certifi.where()
)


class UserTestDetail(Document):
    project_id = IntField(required=True)
    user_id = StringField(required=True)
    number_of_tests_generated = IntField(required=True)
    date_of_generation = DateTimeField(default=datetime.datetime.utcnow)
    repo_name = StringField(required=True)
    branch_name = StringField(required=True)

    meta = {'collection': 'user_test_details'}