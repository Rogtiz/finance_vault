import os

# --- Config (из .env) ---
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")

# --- JWT ---
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# --- KDF ---
KDF_ITERS = 200_000
SALT_SIZE = 16
NONCE_LEN = 12