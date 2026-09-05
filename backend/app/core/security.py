from secrets import compare_digest
import hmac
import hashlib


def secrets_match(left: str, right: str) -> bool:
    """Constant-time comparison helper for future auth integrations."""
    return compare_digest(left, right)


def verify_hmac_sha256(secret: str, body: bytes, signature: str) -> bool:
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
