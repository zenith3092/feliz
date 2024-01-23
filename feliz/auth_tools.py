import bcrypt

# =============== Password Handler ===============

def hash_password(raw_pw: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    hash_value = bcrypt.hashpw(raw_pw.encode(), salt)
    return hash_value.decode()

def check_password(raw_pw: str, hashed_pw: str) -> bool:
    return bcrypt.checkpw(raw_pw.encode(), hashed_pw.encode())