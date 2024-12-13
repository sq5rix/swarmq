import json
import time

from rabbit import RabbitConsumer


def callback(message):
    print(f" [x] Received: {message.decode()}")


# Create Rabbit instance and start consuming
with RabbitConsumer("aqueue") as rabbit:
    rabbit.consume(callback)

print(" [*] Waiting for messages. To exit press CTRL+C")
