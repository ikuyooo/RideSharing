"""Fixed tariffs of the five services (Revision 9 Section 38) - pure functions over the typed
parameters of one pricing_version (`pricing.params`). Exact rational arithmetic; every
charged amount is integer VND floored to the 1.000 VND step (D-18, D-48).

  BIKE_URBAN            BikeFare     = floor((BIKE_BASE + BIKE_PER_KM x km + BIKE_PER_MIN x min) / 1000) x 1000   (10.1)
  CAR_URBAN_PRIVATE     PrivateFare  = floor((BASE + PER_KM x km + PER_MIN x min) / 1000) x 1000                  (12.1)
  CAR_URBAN_POOL        Quote_i      = floor(P_i x (1 - d_min) / 1000) x 1000                                     (18.3)
                        Gap_i        = P_i - Quote_i
                        Unmatched_i  = floor((Quote_i + alpha x Gap_i) / 1000) x 1000
                        Fare_matched_est (new plan) = floor(P_i x (1 - d_matched_typical) / 1000) x 1000          (20.2)
                        (PlanFare, gates, allocation: pricing.pool)
  CAR_INTERCITY_PRIVATE IntercityPrivateFare = floor((INTERCITY_BASE + INTERCITY_PER_KM x km) / 1000) x 1000      (25.2)
  CAR_INTERCITY_POOL    SeatReference = floor(IntercityPrivateFare x (1 - c_private)
                                              / (min_seats_ref x (1 - c_seat)) / 1000) x 1000                    (28.1)
                        0.90 x SeatReference <= SeatPrice <= 1.10 x SeatReference, multiple of 1000              (28.1)
                        DoorSurcharge = floor(DOOR_PER_KM x (extra_pickup_km + extra_dropoff_km) / 1000) x 1000   (28.3)
                        BookingPrice  = SeatPrice x s_j + DoorSurcharge                                           (28.4)
                        TopupSeatPrice = floor(IntercityPrivateFare / S_booked / 1000) x 1000                     (29)
                        topup_amount  = (TopupSeatPrice - SeatPrice) x s_j                                        (29)
                        NewSeatPrice (merge) = min(Y.seat_price, X.seat_price)                                    (30.2)

Distances are taken in metres and durations in seconds (as OSRM returns them) and converted
exactly: km = m / 1000, min = s / 60.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from app.modules.pricing.money import floor_step, q
from app.modules.pricing.params import (
    BikeTariff,
    CarUrbanParams,
    IntercityPoolParams,
    IntercityPrivateParams,
    PricingConfigError,
)


def _km(distance_m: float | Fraction) -> Fraction:
    return q(distance_m) / 1000


def _min(duration_s: float | Fraction) -> Fraction:
    return q(duration_s) / 60


def bike_fare(p: BikeTariff, distance_m: float | Fraction, duration_s: float | Fraction) -> int:
    return floor_step(p.base_vnd + p.per_km_vnd * _km(distance_m) + p.per_min_vnd * _min(duration_s), p.step)


def private_fare(p: CarUrbanParams, distance_m: float | Fraction, duration_s: float | Fraction) -> int:
    return floor_step(p.base_vnd + p.per_km_vnd * _km(distance_m) + p.per_min_vnd * _min(duration_s), p.step)


def intercity_private_fare(p: IntercityPrivateParams, distance_m: float | Fraction) -> int:
    return floor_step(p.base_vnd + p.per_km_vnd * _km(distance_m), p.step)


@dataclass(frozen=True)
class PoolQuote:
    private_fare: int   # P_i = PrivateFare(i), for 1 and 2 seats alike (Section 12.2)
    quote: int          # Quote_i: the cap if matched
    gap: int            # Gap_i = P_i - Quote_i
    unmatched: int      # Unmatched_i: the most the rider can pay (escrow amount, hard constraint 8)


def pool_quote_for(p: CarUrbanParams, private: int) -> PoolQuote:
    quote = floor_step(private * (1 - p.d_min), p.step)
    gap = private - quote
    return PoolQuote(private_fare=private, quote=quote, gap=gap, unmatched=floor_step(quote + p.alpha * gap, p.step))


def fare_matched_estimate(p: CarUrbanParams, private: int) -> int:
    """Section 20.2 case 2 (idle vehicle, no second rider yet)."""
    return floor_step(private * (1 - p.d_matched_typical), p.step)


# ---- CAR_INTERCITY_POOL ------------------------------------------------------

def seat_reference(pool: IntercityPoolParams, private: IntercityPrivateParams, intercity_private: int) -> int:
    exact = intercity_private * (1 - private.commission) / (pool.min_seats_ref * (1 - pool.commission_seat))
    return floor_step(exact, pool.step)


def seat_price_band(pool: IntercityPoolParams, reference: int) -> tuple[int, int]:
    """Whole-1000 VND seat prices allowed around SeatReference (Section 28.1)."""
    lo, hi = pool.seat_band[0] * reference, pool.seat_band[1] * reference
    lo_step = -floor_step(-lo, pool.step)  # smallest multiple of 1000 >= lo
    return lo_step, floor_step(hi, pool.step)


def validate_seat_price(pool: IntercityPoolParams, reference: int, seat_price: int) -> None:
    lo, hi = seat_price_band(pool, reference)
    if seat_price % pool.step or not lo <= seat_price <= hi:
        raise PricingConfigError(f"seat price {seat_price} outside [{lo}, {hi}] or not a multiple of {pool.step}")


@dataclass(frozen=True)
class DoorSurcharge:
    rejected: bool          # a point is farther than max_corridor_deviation_km from its free zone
    amount: int


def door_surcharge(pool: IntercityPoolParams, *, pickup_in_zone: bool, pickup_boundary_direct_km: float | Fraction,
                   pickup_road_km: float | Fraction, dropoff_in_zone: bool,
                   dropoff_boundary_direct_km: float | Fraction, dropoff_road_km: float | Fraction) -> DoorSurcharge:
    """Section 28.3. The caller supplies, per end, whether the point is inside its free zone, the
    straight-line distance to the nearest boundary point and the OSRM car distance to it."""
    extra = Fraction(0)
    for inside, direct, road in ((pickup_in_zone, pickup_boundary_direct_km, pickup_road_km),
                                 (dropoff_in_zone, dropoff_boundary_direct_km, dropoff_road_km)):
        if inside:
            continue
        if q(direct) > pool.max_corridor_deviation_km:
            return DoorSurcharge(rejected=True, amount=0)
        extra += q(road)
    return DoorSurcharge(rejected=False, amount=floor_step(pool.door_surcharge_per_km_vnd * extra, pool.step))


def booking_price(seat_price: int, seat_count: int, surcharge: int) -> int:
    return seat_price * seat_count + surcharge


def topup_seat_price(pool: IntercityPoolParams, intercity_private: int, seats_booked: int) -> int:
    if seats_booked <= 0:
        raise ValueError("top-up needs at least one booked seat")
    return floor_step(Fraction(intercity_private, seats_booked), pool.step)


def topup_amount(topup_price: int, seat_price: int, seat_count: int) -> int:
    return (topup_price - seat_price) * seat_count


def merged_seat_price(source_seat_price: int, target_seat_price: int) -> int:
    """Section 30.2: a rider moved from trip Y to trip X never pays more."""
    return min(source_seat_price, target_seat_price)


# ---- compatibility wrappers (Phase 2 hard constraint 8 reads raw sections) ----------

def distance_time_fare(section: Mapping[str, Any], distance_m: float, duration_s: float) -> int:
    """BikeFare / PrivateFare from a raw `bike_urban` / `car_urban` section."""
    raw = section["base_vnd"] + section["per_km_vnd"] * _km(distance_m) + section["per_min_vnd"] * _min(duration_s)
    return floor_step(raw, int(section["rounding_step_vnd"]))


def pool_quote(car_urban: Mapping[str, Any], private: int) -> PoolQuote:
    return pool_quote_for(CarUrbanParams.from_section(car_urban), private)
