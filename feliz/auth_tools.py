import bcrypt

# =============== Password Handler ===============

def hash_password(raw_pw: str, salt_rounds: int = 12) -> str:
    salt = bcrypt.gensalt(rounds=salt_rounds)
    hash_value = bcrypt.hashpw(raw_pw.encode(), salt)
    return hash_value.decode()

def check_password(raw_pw: str, hashed_pw: str) -> bool:
    return bcrypt.checkpw(raw_pw.encode(), hashed_pw.encode())