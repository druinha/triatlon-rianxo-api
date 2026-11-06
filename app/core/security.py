import hashlib
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

# Argon2id cos parámetros recomendados por OWASP (m=19 MiB, t=2, p=1)
_hasher = PasswordHasher(time_cost=2, memory_cost=19 * 1024, parallelism=1)
# Hash ficticio para igualar tempos cando o email non existe
_DUMMY_HASH = _hasher.hash("timing-equalizer-not-a-real-password")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str | None, password: str) -> bool:
    try:
        return _hasher.verify(password_hash or _DUMMY_HASH, password) and password_hash is not None
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(password_hash: str) -> bool:
    return _hasher.check_needs_rehash(password_hash)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def new_token() -> tuple[str, str]:
    """Devolve (token para a ligazón, hash para gardar na BD)."""
    token = secrets.token_urlsafe(32)
    return token, hash_token(token)
