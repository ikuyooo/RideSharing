"""Import every module's models so Base.metadata is complete (Alembic, tests)."""

from app.db.base import Base
from app.modules.booking import models as booking_models  # noqa: F401
from app.modules.candidate import models as candidate_models  # noqa: F401
from app.modules.driver import models as driver_models  # noqa: F401
from app.modules.fund import models as fund_models  # noqa: F401
from app.modules.identity import models as identity_models  # noqa: F401
from app.modules.intercity import models as intercity_models  # noqa: F401
from app.modules.jobs import models as jobs_models  # noqa: F401
from app.modules.pooling import models as pooling_models  # noqa: F401
from app.modules.pricing import models as pricing_models  # noqa: F401
from app.modules.routing import models as routing_models  # noqa: F401
from app.modules.trip import models as trip_models  # noqa: F401

metadata = Base.metadata
