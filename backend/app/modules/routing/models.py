"""routing module tables (Revision 9, Section 54: `pickup_points`).

`pickup_points` (COULD C9) has no column specification in 56.1. Minimal
structure only, because 56.1 `ride_candidates.pickup_point_id` references it and
56.2 requires `idx_pickup_points_geom` (GIST). Attributes are added in the phase
that implements meeting points.
"""

import uuid
from datetime import datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Index, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PickupPoint(Base):
    __tablename__ = "pickup_points"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    geom: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326, spatial_index=False), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (Index("idx_pickup_points_geom", geom, postgresql_using="gist"),)
