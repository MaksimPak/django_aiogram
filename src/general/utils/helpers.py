import random
import uuid


def random_int():
    return str(random.randint(100, 999))


def generate_uuid():
    return str(uuid.uuid4())[:8]
