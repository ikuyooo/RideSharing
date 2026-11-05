"""Cancellation and no-show fees (Revision 9 Section 18.7, D-52; Baseline `cancellation_policy`).

Pure policy: given who cancelled, when, and the booking's amounts, return the fee, who receives
it and what is refunded. The state machine that applies it (and the escrow call
`cancelAndRefund`) is Phase 4 / 5 / 9.

Rules (`rule` codes in the result):
  any service, cancelled by the driver or the system (incl. CANCELLED_LOW_DEMAND, ESCROW_TIMEOUT): 0, full refund
  BIKE_URBAN, CAR_URBAN_PRIVATE  HELD, or <= grace after CONFIRMED while the driver has not arrived: 0
                                 otherwise, or NO_SHOW: min(cap, rate x Fare_charged); driver / platform
  CAR_URBAN_POOL                 HELD, or <= grace after CONFIRMED while the driver has not arrived: 0 (SF-P3-06)
                                 otherwise, or NO_SHOW: rate x Quote_i; driver / fund
                                 (vehicle alone: 85 / 15, other riders aboard: 50 / 50)
  CAR_INTERCITY_PRIVATE          SCHEDULED > lead before pickup, or NOW <= grace after CONFIRMED: 0
                                 otherwise, or NO_SHOW: rate x IntercityPrivateFare; driver / platform 85 / 15
  CAR_INTERCITY_POOL             > 72 h before T, or inside the merge window: 0
                                 24 h <= remaining <= 72 h: 50 % of BookingPrice; < 24 h or NO_SHOW: 100 %
                                 driver / platform 90 / 10

Driver / platform shares of fees equal the service's own commission split (the 18.7 table uses
exactly those percentages); the 50 / 50 split of a pool fee when other riders are aboard has no
baseline key and is the literal value of the 18.7 table (SF-P3-05).
"""

from dataclasses import dataclass
from datetime import datetime
from fractions import Fraction

from app.modules.pricing.money import exact_vnd
from app.modules.pricing.params import CancellationParams, PricingParams

POOL_SHARED_DRIVER_SHARE = Fraction(1, 2)  # Section 18.7, CAR_URBAN_POOL row, "xe dang co khach khac"
ACTORS = ("PASSENGER", "DRIVER", "SYSTEM")
KINDS = ("CANCEL", "NO_SHOW")


class CancellationNotApplicable(ValueError):
    """The situation is outside the Section 18.7 table (e.g. a no-show before the waiting time)."""


@dataclass(frozen=True)
class CancelContext:
    service_code: str
    actor: str                          # PASSENGER | DRIVER | SYSTEM
    kind: str                           # CANCEL | NO_SHOW
    at: datetime                        # time of the cancellation / no-show
    deposited_vnd: int                  # escrowed amount (what can be refunded)
    ride_status: str = "CONFIRMED"      # HELD | CONFIRMED
    booking_type: str = "NOW"
    confirmed_at: datetime | None = None
    driver_arrived: bool = False
    driver_waited_s: float = 0.0        # NO_SHOW: time the driver waited at the pickup
    fare_charged: int | None = None     # BIKE / CAR_URBAN_PRIVATE / CAR_INTERCITY_PRIVATE fixed fare
    quote: int | None = None            # CAR_URBAN_POOL Quote_i
    vehicle_has_other_riders: bool = False
    planned_pickup: datetime | None = None   # CAR_INTERCITY_PRIVATE
    departure: datetime | None = None        # CAR_INTERCITY_POOL T
    in_merge_free_window: bool = False       # CAR_INTERCITY_POOL, Section 30.2


@dataclass(frozen=True)
class CancelOutcome:
    rule: str
    fee: int
    to_driver: int
    to_platform: int
    to_fund: int
    refund: int

    def check(self, deposited: int) -> None:
        if self.to_driver + self.to_platform + self.to_fund != self.fee:
            raise AssertionError("fee split does not add up")
        if self.fee + self.refund != deposited or not 0 <= self.fee <= deposited:
            raise AssertionError("fee + refund must equal the deposit and the fee cannot exceed it")


def _free(rule: str, deposited: int) -> CancelOutcome:
    return CancelOutcome(rule, 0, 0, 0, 0, deposited)


def _charge(rule: str, fee: int, deposited: int, driver_share: Fraction, rest: str) -> CancelOutcome:
    if fee > deposited:
        raise CancellationNotApplicable(f"fee {fee} exceeds the deposit {deposited}")
    driver = exact_vnd(driver_share * fee)
    other = fee - driver
    out = CancelOutcome(rule, fee, driver, other if rest == "platform" else 0, other if rest == "fund" else 0,
                        deposited - fee)
    out.check(deposited)
    return out


def _seconds_since_confirm(c: CancelContext) -> float:
    if c.confirmed_at is None:
        raise CancellationNotApplicable("a CONFIRMED booking needs confirmed_at")
    return (c.at - c.confirmed_at).total_seconds()


def cancellation_fee(p: PricingParams, cp: CancellationParams, c: CancelContext) -> CancelOutcome:
    if c.actor not in ACTORS or c.kind not in KINDS:
        raise CancellationNotApplicable(f"actor {c.actor} / kind {c.kind}")
    dep = c.deposited_vnd
    if c.actor in ("DRIVER", "SYSTEM"):
        return _free("CANCELLED_BY_DRIVER_OR_SYSTEM", dep)
    urban = c.service_code in ("BIKE_URBAN", "CAR_URBAN_PRIVATE", "CAR_URBAN_POOL")
    if c.kind == "NO_SHOW" and urban and c.driver_waited_s < cp.urban_no_show_wait_min * 60:
        raise CancellationNotApplicable(f"no-show needs the driver to wait {cp.urban_no_show_wait_min} min")
    if c.kind == "NO_SHOW" and c.ride_status == "HELD":
        raise CancellationNotApplicable("no-show of a booking that was never confirmed")

    if urban:
        late = c.kind == "NO_SHOW" or (c.ride_status != "HELD" and (
            c.driver_arrived or _seconds_since_confirm(c) > cp.urban_free_cancel_grace_s))
        if not late:
            return _free("URBAN_FREE_WINDOW", dep)
        if c.service_code == "CAR_URBAN_POOL":
            if c.quote is None:
                raise CancellationNotApplicable("pool fee needs Quote_i")
            fee = exact_vnd(cp.urban_pool_rate_on_quote * c.quote)
            share = POOL_SHARED_DRIVER_SHARE if c.vehicle_has_other_riders else 1 - p.car.commission_pool
            return _charge("URBAN_POOL_LATE", fee, dep, share, "fund")
        if c.fare_charged is None:
            raise CancellationNotApplicable("fee needs Fare_charged")
        fee = min(cp.urban_single_cap_vnd, exact_vnd(cp.urban_single_rate * c.fare_charged))
        commission = p.bike.commission if c.service_code == "BIKE_URBAN" else p.car.commission_private
        return _charge("URBAN_SINGLE_LATE", fee, dep, 1 - commission, "platform")

    if c.service_code == "CAR_INTERCITY_PRIVATE":
        if c.fare_charged is None:
            raise CancellationNotApplicable("fee needs IntercityPrivateFare")
        if c.kind == "CANCEL":
            if c.ride_status == "HELD":
                return _free("INTERCITY_PRIVATE_FREE", dep)
            if c.booking_type == "SCHEDULED":
                if c.planned_pickup is None:
                    raise CancellationNotApplicable("scheduled booking needs planned_pickup")
                if (c.planned_pickup - c.at).total_seconds() > cp.intercity_private_free_lead_h * 3600:
                    return _free("INTERCITY_PRIVATE_FREE", dep)
            elif _seconds_since_confirm(c) <= cp.urban_free_cancel_grace_s:
                return _free("INTERCITY_PRIVATE_FREE", dep)
        fee = exact_vnd(cp.intercity_private_late_rate * c.fare_charged)
        return _charge("INTERCITY_PRIVATE_LATE", fee, dep, 1 - p.intercity_private.commission, "platform")

    if c.service_code == "CAR_INTERCITY_POOL":
        if c.departure is None:
            raise CancellationNotApplicable("intercity pool needs the departure time T")
        price = dep  # BookingPrice is what was escrowed
        remaining_h = Fraction((c.departure - c.at).total_seconds()) / 3600
        if c.kind == "CANCEL" and (remaining_h > cp.intercity_pool_free_before_h or c.in_merge_free_window):
            return _free("INTERCITY_POOL_FREE", dep)
        if c.kind == "NO_SHOW" or remaining_h < cp.pickup_order_fix_h:
            rate, rule = cp.intercity_pool_rate_after_24, "INTERCITY_POOL_AFTER_24H"
        else:
            rate, rule = cp.intercity_pool_rate_72_24, "INTERCITY_POOL_72H_TO_24H"
        return _charge(rule, exact_vnd(rate * price), dep, 1 - p.intercity_pool.commission_seat, "platform")

    raise CancellationNotApplicable(f"unknown service {c.service_code}")
