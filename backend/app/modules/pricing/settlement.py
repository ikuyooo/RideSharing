"""Who receives what when a booking is settled (Revision 9 Sections 10.1, 12.1, 17.1-17.2, 18.3-18.5,
25.2, 28.2, 29; payout part of P3.5). Pure: integer VND in, integer VND out.

Every split is made on the amount actually charged (D-51) and must come out in whole VND;
`exact_vnd` raises instead of rounding if a configuration ever made a share fractional.

  fixed services        driver = (1 - c) x F            platform = c x F
  pool MATCHED_LOCKED   driver = (1 - c_pool) x F       platform = platform_net x F     fund = fund_rate x F
  pool UNMATCHED_LOCKED driver = (1 - c_pool) x U       platform = c_pool x U (no 3 % to the fund)
                        GuaranteePayout = max(0, (1 - c_private) x P_i - (1 - c_pool) x U)   (NO_COMPATIBLE, ...)
  intercity pool        driver = (1 - c_seat) x price   (CONFIRMED / CONFIRMED_UNDER_MIN)
                        driver = (1 - c_topup) x price  (CONFIRMED_TOPUP, P0-04)
"""

from dataclasses import dataclass
from fractions import Fraction

from app.modules.pricing.money import exact_vnd
from app.modules.pricing.params import PricingParams
from app.modules.pricing.tariff import pool_quote_for

# unmatched_cause values whose UNMATCHED_LOCKED booking is guaranteed by the fund (table 18.5).
# CORIDER_CANCELLED_EARLY is the interpretation of SF-P3-04 (row 3: "theo ket qua chot").
GUARANTEED_CAUSES = frozenset({"NO_COMPATIBLE", "PASSENGER_REJECTED_POOL", "CORIDER_CANCELLED_EARLY"})
PAYOUT_KINDS = ("FIXED", "POOL_MATCHED", "POOL_UNMATCHED", "INTERCITY_SEAT", "INTERCITY_TOPUP",
                "INTERCITY_UNDER_MIN", "CANCELLATION_FEE")


@dataclass(frozen=True)
class Settlement:
    kind: str
    gross_charged: int            # what the passenger pays for this booking (final price or fee)
    commission_rate: Fraction
    driver_base: int              # driver's share of the passenger money
    platform_net: int
    fund_contribution: int        # >= 0, into the guarantee fund
    guarantee: int                # >= 0, paid by the guarantee fund to the driver
    unmatched_cause: str = "NONE"

    @property
    def total_driver(self) -> int:
        return self.driver_base + self.guarantee

    def check(self) -> None:
        if self.driver_base + self.platform_net + self.fund_contribution != self.gross_charged:
            raise AssertionError("driver + platform + fund must equal the amount charged (G18)")
        if min(self.gross_charged, self.driver_base, self.platform_net, self.fund_contribution, self.guarantee) < 0:
            raise AssertionError("settlement amounts are never negative")


def _split(kind: str, amount: int, commission: Fraction, **kw: object) -> Settlement:
    platform = exact_vnd(commission * amount)
    s = Settlement(kind, amount, commission, amount - platform, platform, 0, 0, **kw)  # type: ignore[arg-type]
    s.check()
    return s


def settle_fixed(p: PricingParams, service_code: str, fare: int) -> Settlement:
    commission = {"BIKE_URBAN": p.bike.commission, "CAR_URBAN_PRIVATE": p.car.commission_private,
                  "CAR_INTERCITY_PRIVATE": p.intercity_private.commission}[service_code]
    return _split("FIXED", fare, commission)


def settle_pool_matched(p: PricingParams, final_price: int, unmatched_cause: str = "NONE",
                        private: int | None = None, corider_cancel_to_driver: int = 0) -> Settlement:
    """MATCHED_LOCKED: 85 / 12 / 3 of the final price. With CORIDER_CANCELLED_LATE (table 18.5 row 4)
    the fund tops the driver up to the single-ride income of this booking, after counting the part of
    the co-rider's cancellation fee the driver already receives (interpretation SF-P3-04)."""
    c = p.car
    platform = exact_vnd(c.platform_net_pool * final_price)
    fund = exact_vnd(c.fund_rate * final_price)
    driver = final_price - platform - fund
    if driver != exact_vnd((1 - c.commission_pool) * final_price):
        raise AssertionError("pool split does not add up")
    guarantee = 0
    if unmatched_cause == "CORIDER_CANCELLED_LATE":
        if private is None:
            raise ValueError("CORIDER_CANCELLED_LATE needs P_i")
        target = exact_vnd((1 - c.commission_private) * private)
        guarantee = max(0, target - driver - corider_cancel_to_driver)
    elif unmatched_cause != "NONE":
        raise ValueError(f"a MATCHED_LOCKED booking cannot have unmatched_cause {unmatched_cause}")
    s = Settlement("POOL_MATCHED", final_price, c.commission_pool, driver, platform, fund, guarantee, unmatched_cause)
    s.check()
    return s


def settle_pool_unmatched(p: PricingParams, private: int, final_price: int, unmatched_cause: str) -> Settlement:
    """UNMATCHED_LOCKED (Sections 18.3-18.5). The final price must be the one the cause dictates."""
    c = p.car
    pq = pool_quote_for(c, private)
    expected = pq.quote if unmatched_cause == "DRIVER_DECLINED" else pq.unmatched
    if unmatched_cause not in GUARANTEED_CAUSES | {"DRIVER_DECLINED"}:
        raise ValueError(f"unmatched_cause {unmatched_cause} is not an UNMATCHED_LOCKED cause")
    if final_price != expected:
        raise ValueError(f"UNMATCHED_LOCKED with {unmatched_cause} locks {expected}, not {final_price}")
    platform = exact_vnd(c.commission_pool * final_price)
    driver = final_price - platform
    guarantee = 0
    if unmatched_cause in GUARANTEED_CAUSES:
        guarantee = max(0, exact_vnd((1 - c.commission_private) * private) - driver)
    s = Settlement("POOL_UNMATCHED", final_price, c.commission_pool, driver, platform, 0, guarantee, unmatched_cause)
    s.check()
    return s


def settle_intercity_pool(p: PricingParams, price: int, confirmation: str) -> Settlement:
    """Seat booking of a CAR_INTERCITY_POOL trip that ran (Sections 28.2, 29). `confirmation` is the
    outcome of the T-72h decision (the later PICKUP_ORDER_FIXED / DEPARTED states do not carry it)."""
    if confirmation == "CONFIRMED_TOPUP":
        return _split("INTERCITY_TOPUP", price, p.intercity_pool.commission_topup)
    if confirmation == "CONFIRMED_UNDER_MIN":
        return _split("INTERCITY_UNDER_MIN", price, p.intercity_pool.commission_seat)
    if confirmation == "CONFIRMED":
        return _split("INTERCITY_SEAT", price, p.intercity_pool.commission_seat)
    raise ValueError(f"{confirmation} is not a confirmation outcome that settles a seat")
