from mongoengine import StringField, Document, IntField, DateTimeField, BooleanField
from server.utils.mongo_helper import get_mongo_connection

mongo_conn = get_mongo_connection()

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
