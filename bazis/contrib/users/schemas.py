from pydantic import BaseModel


class TokenResponse(BaseModel):
    """
    Represents a response containing an access token and its type, typically used
    for authentication purposes.
    """

    access_token: str
    token_type: str
