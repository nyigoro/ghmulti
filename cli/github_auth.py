from dataclasses import dataclass
from typing import Optional

import requests


@dataclass
class TokenValidationResult:
    valid: Optional[bool]
    message: str
    status_code: Optional[int] = None


def validate_github_token(token: str, timeout_seconds: int = 5) -> TokenValidationResult:
    if not token:
        return TokenValidationResult(valid=None, message="No token provided.")

    try:
        response = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {token}"},
            timeout=timeout_seconds
        )
    except requests.RequestException as exc:
        return TokenValidationResult(
            valid=None,
            message=f"Token validation unavailable: {exc.__class__.__name__}: {exc}"
        )

    if response.status_code == 200:
        return TokenValidationResult(valid=True, message="Token is valid.", status_code=200)

    if response.status_code == 401:
        return TokenValidationResult(valid=False, message="Token is invalid or expired.", status_code=401)

    return TokenValidationResult(
        valid=None,
        message=f"Token validation returned unexpected status code: {response.status_code}",
        status_code=response.status_code
    )
