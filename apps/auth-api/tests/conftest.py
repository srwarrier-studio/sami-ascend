import os

for name in ["ENTRA_SECRET", "ENTRA_CLIENT_ID", "ENTRA_AUTHORITY", "ENTRA_REDIRECT_URL"]:
    os.environ.setdefault(name, "test")
os.environ.setdefault("JWT_SECRET", "t" * 32)
os.environ.setdefault("SESSION_SECRET", "t" * 32)
