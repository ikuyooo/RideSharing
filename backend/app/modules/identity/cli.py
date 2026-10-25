"""Create an ADMIN account (admins cannot self-register).

Usage: python -m app.modules.identity.cli create-admin --email admin@example.org
The password is read interactively, or from ADMIN_PASSWORD when stdin is not a TTY.
"""

import argparse
import getpass
import os
import sys

from app.db.session import get_sessionmaker
from app.modules.identity import service


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create-admin")
    create.add_argument("--email", required=True)
    args = parser.parse_args()

    password = os.environ.get("ADMIN_PASSWORD") if not sys.stdin.isatty() else getpass.getpass("Password: ")
    if not password or len(password) < 8:
        sys.exit("password must be at least 8 characters")
    with get_sessionmaker()() as session:
        user = service.create_admin(session, args.email, password)
    print(f"created ADMIN {user.id}")


if __name__ == "__main__":
    main()
