import json
import time

from rabbit import RabbitPublisher

# Create Rabbit instance and start consuming
rabbit = RabbitPublisher("aqueue")
rabbit.publish("hello world!!")
