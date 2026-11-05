"""P3.6 - cancellation / no-show fees of Revision 9 Section 18.7 (D-52), row by row and at every
time boundary. Fee + refund always equals the deposit; the fee never exceeds the configured cap;
free cases charge nothing."""

from datetime import UTC, datetime, timedelta

import pytest
import yaml

from app.modules.pricing.cancellation import CancelContext, CancellationNotApplicable, cancellation_fee
from app.modules.pricing.params import CancellationParams, PricingParams
from tests.conftest import CONFIG_BASELINE

BASELINE = yaml.safe_load(CONFIG_BASELINE.read_text(encoding="utf-8"))
P = PricingParams.from_sections(BASELINE["pricing_version"], BASELINE["pool_policy_version"], BASELINE)
CP = CancellationParams.from_baseline(BASELINE)
T0 = datetime(2026, 11, 4, 8, 0, tzinfo=UTC)


def fee(**kw: object):  # noqa: ANN201
    base = dict(actor="PASSENGER", kind="CANCEL", at=T0, ride_status="CONFIRMED", confirmed_at=T0 - timedelta(seconds=10))
    ctx = CancelContext(**(base | kw))  # type: ignore[arg-type]
    out = cancellation_fee(P, CP, ctx)
    out.check(ctx.deposited_vnd)
    return out


@pytest.mark.parametrize("service", ["BIKE_URBAN", "CAR_URBAN_PRIVATE"])
def test_urban_single(service: str) -> None:
    fare = 81000 if service == "BIKE_URBAN" else 194000
    common = dict(service_code=service, deposited_vnd=fare, fare_charged=fare)
    assert fee(**common, ride_status="HELD", confirmed_at=None).fee == 0
    assert fee(**common, at=T0 + timedelta(seconds=110)).fee == 0                       # 120 s after confirm: free
    late = fee(**common, at=T0 + timedelta(seconds=111))                                 # 121 s
    expected = min(20000, fare // 5)
    assert (late.rule, late.fee, late.refund) == ("URBAN_SINGLE_LATE", expected, fare - expected)
    assert (late.to_driver, late.to_platform, late.to_fund) == (expected * 4 // 5, expected // 5, 0)
    arrived = fee(**common, driver_arrived=True)                                         # driver already there
    assert arrived.fee == expected
    no_show = fee(**common, kind="NO_SHOW", driver_waited_s=300)
    assert no_show.fee == expected
    with pytest.raises(CancellationNotApplicable):                                       # waited < 5 min
        fee(**common, kind="NO_SHOW", driver_waited_s=299)


def test_bike_fee_is_below_the_cap_and_private_fee_is_capped() -> None:
    assert fee(service_code="BIKE_URBAN", deposited_vnd=81000, fare_charged=81000, driver_arrived=True).fee == 16200
    assert fee(service_code="CAR_URBAN_PRIVATE", deposited_vnd=194000, fare_charged=194000,
               driver_arrived=True).fee == 20000                                         # min(20.000, 38.800)


def test_urban_pool() -> None:
    common = dict(service_code="CAR_URBAN_POOL", deposited_vnd=174000, quote=155000)
    assert fee(**common).fee == 0                                                         # within 120 s (SF-P3-06)
    alone = fee(**common, at=T0 + timedelta(minutes=5))
    assert (alone.fee, alone.to_driver, alone.to_fund, alone.to_platform) == (31000, 26350, 4650, 0)
    shared = fee(**common, at=T0 + timedelta(minutes=5), vehicle_has_other_riders=True)
    assert (shared.fee, shared.to_driver, shared.to_fund) == (31000, 15500, 15500)
    assert shared.refund == 174000 - 31000


def test_intercity_private() -> None:
    common = dict(service_code="CAR_INTERCITY_PRIVATE", deposited_vnd=637000, fare_charged=637000)
    sched = dict(common, booking_type="SCHEDULED", planned_pickup=T0 + timedelta(hours=2, seconds=1))
    assert fee(**sched).fee == 0                                                          # > 2 h before pickup
    at_2h = fee(**dict(sched, planned_pickup=T0 + timedelta(hours=2)))
    assert (at_2h.fee, at_2h.to_driver, at_2h.to_platform) == (127400, 108290, 19110)      # <= 2 h: 20 %
    assert fee(**common, booking_type="NOW").fee == 0                                     # NOW within 120 s
    assert fee(**common, booking_type="NOW", at=T0 + timedelta(minutes=3)).fee == 127400
    assert fee(**sched, kind="NO_SHOW").fee == 127400


def test_intercity_pool_windows() -> None:
    dep = T0 + timedelta(days=5)
    common = dict(service_code="CAR_INTERCITY_POOL", deposited_vnd=200000, departure=dep)
    assert fee(**common, at=dep - timedelta(hours=72, seconds=1)).fee == 0                # before T-72h: free
    at72 = fee(**common, at=dep - timedelta(hours=72))
    assert (at72.rule, at72.fee, at72.to_driver, at72.to_platform) == ("INTERCITY_POOL_72H_TO_24H", 100000, 90000, 10000)
    at24 = fee(**common, at=dep - timedelta(hours=24))
    assert at24.fee == 100000                                                             # T-24h itself: still 50 %
    after = fee(**common, at=dep - timedelta(hours=23, minutes=59))
    assert (after.rule, after.fee, after.refund) == ("INTERCITY_POOL_AFTER_24H", 200000, 0)
    assert fee(**common, at=dep - timedelta(hours=30), in_merge_free_window=True).fee == 0  # Section 30.2
    assert fee(**common, at=dep - timedelta(hours=48), kind="NO_SHOW").fee == 200000
    # Section 72.3: 3 seats confirmed at T-72h, one rider cancels at T-36h -> 50 % of the seat, 90 % to the driver
    t36 = fee(**common, at=dep - timedelta(hours=36))
    assert (t36.fee, t36.to_driver) == (100000, 90000)


@pytest.mark.parametrize("service", ["BIKE_URBAN", "CAR_URBAN_PRIVATE", "CAR_URBAN_POOL", "CAR_INTERCITY_PRIVATE",
                                     "CAR_INTERCITY_POOL"])
@pytest.mark.parametrize("actor", ["DRIVER", "SYSTEM"])
def test_driver_or_system_cancellation_is_free_everywhere(service: str, actor: str) -> None:
    out = fee(service_code=service, actor=actor, deposited_vnd=174000, at=T0 + timedelta(hours=1),
              fare_charged=174000, quote=155000, departure=T0 + timedelta(hours=2))
    assert (out.fee, out.refund) == (0, 174000)


def test_fee_never_exceeds_the_deposit() -> None:
    with pytest.raises(CancellationNotApplicable):
        fee(service_code="CAR_URBAN_POOL", deposited_vnd=10000, quote=155000, at=T0 + timedelta(minutes=5))
