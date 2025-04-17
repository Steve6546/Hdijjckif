# auth_manager.py
import logging
import os
from datetime import datetime, timedelta, timezone # Ensure timezone awareness
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

# --- Configuration ---
# Load from environment variables or use defaults (INSECURE defaults for example only)
SECRET_KEY = os.getenv("SECRET_KEY", "a_very_secret_key_for_development_only_please_change_in_production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))  # 24 hours

# For demo purposes, ensure we use a consistent key for the demo token in script.js
if SECRET_KEY == "a_very_secret_key_for_development_only_please_change_in_production":
    SECRET_KEY = "your_secret_key_here"
    logger.warning("Using default SECRET_KEY. This is INSECURE. Set the SECRET_KEY environment variable.")

# --- Password Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- OAuth2 Scheme ---
# This URL must match the path operation of your token endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- User Database (Placeholder) ---
# Replace this with your actual user database interaction (e.g., SQLAlchemy, MongoDB)
def get_password_hash(password):
    return pwd_context.hash(password)

# Example: Store hashed passwords
fake_users_db = {
    "testuser": {
        "username": "testuser",
        "hashed_password": get_password_hash("password"), # Hash the password
        "full_name": "Test User",
        "email": "test@example.com",
        "disabled": False,
        "roles": ["user"] # Example role
    },
     "adminuser": {
        "username": "adminuser",
        "hashed_password": get_password_hash("adminpass"),
        "full_name": "Admin User",
        "email": "admin@example.com",
        "disabled": False,
        "roles": ["admin", "user"]
    }
}

def get_user(username: str):
    """Retrieves user data from the fake database."""
    if username in fake_users_db:
        user_dict = fake_users_db[username]
        # You might return a Pydantic model here in a real app
        return user_dict
    return None

# --- Authentication Logic ---
def verify_password(plain_password, hashed_password):
    """Verifies a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str):
    """Authenticates a user based on username and password."""
    user = get_user(username)
    if not user:
        logger.debug(f"Authentication failed: User '{username}' not found.")
        return False
    if user.get("disabled", False):
        logger.debug(f"Authentication failed: User '{username}' is disabled.")
        return False
    if not verify_password(password, user["hashed_password"]):
        logger.debug(f"Authentication failed: Incorrect password for user '{username}'.")
        return False
    logger.info(f"User '{username}' authenticated successfully.")
    return user # Return user dict on success

# --- Token Creation ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Creates a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.debug(f"Created access token for subject: {data.get('sub')}")
    return encoded_jwt

# --- Token Verification and User Retrieval ---
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Decodes the JWT token, validates it, and retrieves the current user.
    Used as a dependency in protected endpoints.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            logger.warning("Token validation failed: 'sub' (username) claim missing.")
            raise credentials_exception
        # token_data = TokenData(username=username) # Optional: Use Pydantic model for payload
    except JWTError as e:
        logger.warning(f"Token validation failed: {e}")
        raise credentials_exception

    user = get_user(username) # Fetch user from "database"
    if user is None:
        logger.warning(f"Token validation failed: User '{username}' from token not found in DB.")
        raise credentials_exception
    if user.get("disabled", False):
         logger.warning(f"Token validation failed: User '{username}' is disabled.")
         raise HTTPException(status_code=400, detail="Inactive user")

    # Return the username or the full user object/dict as needed
    # Returning username for consistency with the example spec
    logger.debug(f"Successfully validated token for user: {username}")
    return user["username"]

async def get_current_active_admin_user(current_user: str = Depends(get_current_user)):
    """
    Dependency to ensure the current user is an active admin.
    """
    user_data = get_user(current_user) # Get full user data
    if not user_data or "admin" not in user_data.get("roles", []):
        logger.warning(f"Admin access denied for user: {current_user}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have admin privileges"
        )
    logger.debug(f"Admin access granted for user: {current_user}")
    return current_user # Or return user_data if needed

# Example usage (optional, for testing)
if __name__ == "__main__":
    print("Testing Auth Manager...")

    # Test hashing
    hashed = get_password_hash("s3cr3t")
    print(f"Hashed 's3cr3t': {hashed}")
    print(f"Verify 's3cr3t': {verify_password('s3cr3t', hashed)}")
    print(f"Verify 'wrong': {verify_password('wrong', hashed)}")

    # Test authentication
    print("\nTesting Authentication:")
    auth_user = authenticate_user("testuser", "password")
    print(f"Authenticate 'testuser'/'password': {auth_user is not False}")
    auth_fail_user = authenticate_user("testuser", "wrongpass")
    print(f"Authenticate 'testuser'/'wrongpass': {auth_fail_user is not False}")
    auth_fail_nouser = authenticate_user("nouser", "password")
    print(f"Authenticate 'nouser'/'password': {auth_fail_nouser is not False}")

    # Test token creation
    print("\nTesting Token Creation:")
    if auth_user:
        token = create_access_token(data={"sub": auth_user["username"]})
        print(f"Generated Token for {auth_user['username']}: {token[:20]}...") # Print partial token

        # Manual decode test (requires get_current_user to be async, hard to test directly here)
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            print(f"Decoded Payload 'sub': {payload.get('sub')}")
            print(f"Decoded Payload 'exp': {datetime.fromtimestamp(payload.get('exp', 0), timezone.utc)}")
        except JWTError as e:
            print(f"Error decoding token: {e}")

    print("\nAuth Manager test finished.")