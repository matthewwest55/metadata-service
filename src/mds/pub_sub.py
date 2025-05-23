# This is a wrapper class for changing the pub/sub service easily
from . import config
from .redis_pub_sub import *
import redis

class PubSubClient():
    client:redis.Redis = None
    sub_client:redis.Redis = None

    def __init__(self):
        self.client = get_redis_client('alt.data-one.dev.planx-pla.net', 6379, 0)

    def publish(self, channel: str, message: str):
        redis_publish(self.client, channel, message)

    def subscribe(self, channel):
        self.sub_client = self.client.pubsub()
        self.sub_client.subscribe(channel)

    def listen(self):
        self.sub_client.listen()