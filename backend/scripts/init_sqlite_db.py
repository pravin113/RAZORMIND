import sys
from pathlib import Path

from sqlalchemy import create_engine

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db import models  # noqa: F401
from app.db.database import Base


def main() -> None:
    engine = create_engine("sqlite:///live_test.db")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("live_test.db initialized")


if __name__ == "__main__":
    main()
