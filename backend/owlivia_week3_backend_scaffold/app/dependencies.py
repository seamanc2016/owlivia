from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user_id(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> str:
    """Validate the shape of a Bearer token until Supabase Auth is connected."""
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="A valid Bearer token is required.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_error

    if credentials.scheme.lower() != "bearer" or not credentials.credentials.strip():
        raise credentials_error

    # Week 3 placeholder: replace this return with the Supabase user ID.
    return "prototype-user"
