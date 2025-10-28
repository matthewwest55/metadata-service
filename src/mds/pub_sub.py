# This is a wrapper class for changing the pub/sub service easily
from . import config
from .redis_pub_sub import *
import redis
import json

class PubSubClient():
    client:redis.Redis = None
    sub_client:redis.Redis = None

    def __init__(self):
        self.client = get_redis_client('alt.data-instance-x.dev.planx-pla.net', 6379, 0)

    def publish(self, channel: str, message: str):
        redis_publish(self.client, channel, message)

    async def batch_publish(self, channel:str, data):
        for metadata in data:
            self.publish(channel, "POST " + str(metadata.guid) + " " + json.dumps(metadata.data))

    # def subscribe(self, channel):
    #     self.sub_client = self.client.pubsub()
    #     self.sub_client.subscribe(channel)

    # def listen(self):
    #     self.sub_client.listen()