from collections.abc import Sequence

from sqlalchemy import CheckConstraint

# Revision 9, Section 2.1 / D-07.
SERVICE_CODES = (
    "BIKE_URBAN",
    "CAR_URBAN_PRIVATE",
    "CAR_URBAN_POOL",
    "CAR_INTERCITY_PRIVATE",
    "CAR_INTERCITY_POOL",
)


def in_check(column: str, values: Sequence[str], name: str) -> CheckConstraint:
    """CHECK (<column> IN (...)). Enumerations are stored as VARCHAR + CHECK
    rather than PostgreSQL ENUM types so migrations stay simple to evolve.
    NULL passes the check, so nullability is controlled by the column itself."""
    quoted = ", ".join(f"'{v}'" for v in values)
    return CheckConstraint(f"{column} IN ({quoted})", name=name)
