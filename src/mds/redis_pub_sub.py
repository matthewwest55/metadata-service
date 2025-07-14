# This is the redis implementation of pub/sub for gen3
import redis

def get_redis_client(host, port, db):
    # Don't commit secrets in the future!
    redis_client = redis.Redis(host=host, port=port, db=db, password="temporary_password")
    return redis_client

def redis_publish(client: redis.Redis, channel:str, message:str):
    # print(message)
    # client.publish(channel, message)
    try:
        client.xadd(channel, {"message": message})
    except Exception as e:
        # Not clear to me if this is failing or not, so adding this
        print("Failed to publish" + str(e))

# def redis_subscribe(client: redis.Redis, channel:str):
#     pass