import jwt

# Use the generated secret key
secret = 'wK6KJc4Hkk0s7ZkLb5sM58pZKwE68_DSk6Z8q5sZyY9r1Uv6bIuU0HdTmV8lLwhF'
algorithm = 'HS256'


def JWT_ENCODE_1(payload):
    return jwt.encode(payload, secret, algorithm=algorithm)


def JWT_DECODE_1(token):
    if token.startswith('Bearer '):
        token = token[7:]  # Remove 'Bearer ' prefix
    return jwt.decode(token, secret, algorithms=[algorithm])
