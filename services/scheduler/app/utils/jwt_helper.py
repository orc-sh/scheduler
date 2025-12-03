from datetime import datetime, timedelta, timezone

import jwt


def generate_jwt_token(payload: dict, secret: str, algorithm: str = "HS256", expire_minutes: int = 15) -> str:
    """
    Generate a JWT token valid for `expire_minutes` (default 15 minutes).

    Args:
        payload (dict): The payload to encode in the token.
        secret (str): The key/secret to sign the token.
        algorithm (str): Algorithm to use, defaults to "HS256".
        expire_minutes (int): Token validity duration in minutes.

    Returns:
        str: Encoded JWT token
    """
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(minutes=expire_minutes)
    jwt_payload = payload.copy()
    jwt_payload.update({"iat": int(issued_at.timestamp()), "exp": int(expires_at.timestamp()), "aud": "authenticated"})
    token = jwt.encode(jwt_payload, secret, algorithm=algorithm)
    # For PyJWT>=2.0, encode returns str, otherwise bytes
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


def validate_jwt_token(token: str, secret: str, algorithms: list = ["HS256"], audience: str = "authenticated") -> dict:
    """
    Validate a JWT token and return its payload.

    Args:
        token (str): JWT token string to validate.
        secret (str): Secret to verify the signature.
        algorithms (list): List of allowed algorithms (default ["HS256"]).
        audience (str, optional): Audience claim to verify.

    Returns:
        dict: Decoded token payload.

    Raises:
        jwt.ExpiredSignatureError: If the token has expired.
        jwt.InvalidTokenError: If the token is invalid or verification fails.
    """
    options = {"require": ["exp", "iat"]}
    return jwt.decode(
        token,
        secret,
        algorithms=algorithms,
        options=options,
        audience=audience,
    )
