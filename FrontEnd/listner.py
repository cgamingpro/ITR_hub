from rediscon import redis_conn
from db import getdb

pubsub = redis_conn.pubsub()
pubsub.subscribe("batch_complete")

for message in pubsub.listen():

    if message["type"] != "message":
        continue

    request_id = message["data"]

    con = getdb()
    cursor = con.cursor()

    cursor.execute("""
        UPDATE requests
        SET status = 'completed'
        WHERE id = %s::uuid
    """, (request_id,))

    con.commit()

    cursor.close()
    con.close()