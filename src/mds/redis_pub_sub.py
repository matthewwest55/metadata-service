# This is the redis implementation of pub/sub for gen3
import redis

def get_redis_client(host, port, db):
    return redis.Redis(host=host, port=port, db=db)

def publish(client: redis.Redis, channel:str, message:str):
    client.publish(channel, message)