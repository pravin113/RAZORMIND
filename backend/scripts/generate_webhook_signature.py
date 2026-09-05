import argparse
import hashlib
import hmac
import os
from pathlib import Path


def read_payload(args) -> bytes:
    if args.payload_file:
        return Path(args.payload_file).read_bytes()
    if args.payload:
        return args.payload.encode("utf-8")
    raise SystemExit("Provide --payload-file or --payload")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a Razorpay-style webhook signature.")
    parser.add_argument("--secret", default=os.getenv("RAZORPAY_WEBHOOK_SECRET"))
    parser.add_argument("--payload-file")
    parser.add_argument("--payload")
    args = parser.parse_args()

    if not args.secret:
        raise SystemExit("Provide --secret or set RAZORPAY_WEBHOOK_SECRET")

    signature = hmac.new(args.secret.encode("utf-8"), read_payload(args), hashlib.sha256).hexdigest()
    print(signature)


if __name__ == "__main__":
    main()

