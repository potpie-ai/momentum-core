import datetime
import os

import certifi
from mongoengine import StringField, Document, IntField, DateTimeField, connect, BooleanField

connect(
    'test',
    host=os.getenv("MONGO_URI", "mongodb://localhost:27017"),
    tlsCAFile=certifi.where()
)


class UserSubscriptionDetail(Document):
    userId = StringField(required=True)
    userEmail = StringField(required=True)
    active = BooleanField(required=True)
    availedTrial = BooleanField(required=True)
    plan = StringField(required=True)
    nextBillDate = DateTimeField(required=True)
    subscriptionStartedAt = StringField(required=True)
    subscriptionId = StringField(required=True)
    cancelOn = StringField(default="")
    paddle_customer_id = StringField(required=True)

    meta = {'collection': 'subscriptions', "strict": False}
