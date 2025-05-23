# This is the redis implementation of pub/sub for gen3
import redis

def get_redis_client(host, port, db):
    return redis.Redis(host=host, port=port, db=db)

def redis_publish(client: redis.Redis, channel:str, message:str):
    # print(message)
    # client.publish(channel, message)
    client.xadd(channel, {"message": message})

# def redis_subscribe(client: redis.Redis, channel:str):
#     pass