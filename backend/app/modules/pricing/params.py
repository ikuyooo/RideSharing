"""Typed, validated pricing parameters of one `pricing_version` (Revision 9 Appendix B,
MVP_CONFIG_BASELINE_V1 sections 3-4).

Built from the `params_json.sections` of the immutable `pricing_configs` rows (see
`pricing.service.load_pricing`) - never from constants in code. Every value is checked
against the valid domain of Baseline section 3; an out-of-domain or inconsistent value
raises `PricingConfigError` instead of being priced with.

The cancellation policy and the guarantee-fund seed are not part of the `pricing_configs`
rows (Baseline section 5.1 lists pricing parameters only); they are read from the locked
baseline YAML (`CancellationParams.from_baseline`) - P3 finding SF-P3-05.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from app.modules.pricing.money import q

ON_LOWER_BOUND = ("REJECT", "CLAMP_TO_BASE")


class PricingConfigError(ValueError):
    pass


def _rate(section: Mapping[str, Any], key: str, lo: str, hi: str) -> Fraction:
    value = q(section[key])
    if not q(lo) <= value <= q(hi):
        raise PricingConfigError(f"{key} = {section[key]} outside [{lo}, {hi}]")
    return value


def _vnd(section: Mapping[str, Any], key: str, lo: int = 0, hi: int | None = None, multiple: int = 1) -> int:
    value = section[key]
    if not isinstance(value, int) or isinstance(value, bool) or value < lo or (hi is not None and value > hi) \
            or value % multiple:
        raise PricingConfigError(f"{key} = {value!r} is not an integer VND in [{lo}, {hi}] (multiple of {multiple})")
    return value


def _step(section: Mapping[str, Any]) -> int:
    if section["rounding_step_vnd"] != 1000:  # Baseline 3.2 / 3.3: locked to {1000}
        raise PricingConfigError("rounding_step_vnd is locked to 1000 (D-18, D-48)")
    return 1000


@dataclass(frozen=True)
class BikeTariff:
    base_vnd: int
    per_km_vnd: int
    per_min_vnd: int
    commission: Fraction
    step: int

    @classmethod
    def from_section(cls, s: Mapping[str, Any]) -> "BikeTariff":
        return cls(base_vnd=_vnd(s, "base_vnd", multiple=1000), per_km_vnd=_vnd(s, "per_km_vnd", 1000, 20000),
                   per_min_vnd=_vnd(s, "per_min_vnd", 0, 5000), commission=_rate(s, "commission_rate", "0.05", "0.35"),
                   step=_step(s))


@dataclass(frozen=True)
class CarUrbanParams:
    """`car_urban`: shared by CAR_URBAN_PRIVATE and CAR_URBAN_POOL (Appendix B)."""
    base_vnd: int
    per_km_vnd: int
    per_min_vnd: int
    stop_fee_vnd: int
    commission_private: Fraction
    commission_pool: Fraction
    platform_net_pool: Fraction
    fund_rate: Fraction
    d_min: Fraction
    d_max: Fraction
    on_lower_bound_infeasible: str
    allow_dynamic_insertion_after_partial_lock: bool
    d_matched_typical: Fraction
    gamma_seat: Fraction
    lam: Fraction
    mu: Fraction
    alpha: Fraction
    enforce_hourly_gate: bool
    eps_hourly: Fraction
    step: int
    max_party_seats_pool: int

    @classmethod
    def from_section(cls, s: Mapping[str, Any]) -> "CarUrbanParams":
        p = cls(
            base_vnd=_vnd(s, "base_vnd", 10000, 50000, 1000), per_km_vnd=_vnd(s, "per_km_vnd", 5000, 25000),
            per_min_vnd=_vnd(s, "per_min_vnd", 0, 5000), stop_fee_vnd=_vnd(s, "extra_stop_fee_vnd", 0, 20000, 1000),
            commission_private=_rate(s, "commission_private", "0.10", "0.30"),
            commission_pool=q(s["commission_pool_total"]),
            platform_net_pool=_rate(s, "platform_net_pool_rate", "0.05", "0.20"),
            fund_rate=_rate(s, "fund_contribution_rate", "0.01", "0.08"),
            d_min=_rate(s, "d_min", "0.10", "0.30"), d_max=_rate(s, "d_max", "0.45", "0.70"),
            on_lower_bound_infeasible=s["on_lower_bound_infeasible"],
            allow_dynamic_insertion_after_partial_lock=s["allow_dynamic_insertion_after_partial_lock"],
            d_matched_typical=q(s["d_matched_typical"]),
            gamma_seat=_rate(s, "party_seat_surcharge_gamma", "0.00", "0.50"),
            lam=_rate(s, "detour_weight_lambda", "0.5", "2.0"), mu=_rate(s, "walk_weight_mu", "1.0", "4.0"),
            alpha=_rate(s, "unmatched_passenger_share_alpha", "0.30", "0.70"),
            enforce_hourly_gate=s["enforce_driver_hourly_rate_gate"],
            eps_hourly=_rate(s, "driver_hourly_rate_tolerance_eps", "0.00", "0.10"), step=_step(s),
            max_party_seats_pool=int(s["max_party_seats_pool"]))
        if p.commission_pool != p.platform_net_pool + p.fund_rate:
            raise PricingConfigError("commission_pool_total must equal platform_net_pool_rate + fund_contribution_rate")
        if not p.d_min < p.d_max:
            raise PricingConfigError("d_min must be < d_max")
        if not p.d_min <= p.d_matched_typical <= p.d_max:
            raise PricingConfigError("d_matched_typical must lie in [d_min, d_max]")
        if p.on_lower_bound_infeasible not in ON_LOWER_BOUND:
            raise PricingConfigError(f"on_lower_bound_infeasible must be one of {ON_LOWER_BOUND}")
        if not isinstance(p.allow_dynamic_insertion_after_partial_lock, bool) or not isinstance(p.enforce_hourly_gate, bool):
            raise PricingConfigError("boolean pool flags must be booleans")
        if p.max_party_seats_pool not in (1, 2):
            raise PricingConfigError("max_party_seats_pool must be 1 or 2")
        return p


@dataclass(frozen=True)
class IntercityPrivateParams:
    base_vnd: int
    per_km_vnd: int
    commission: Fraction
    step: int

    @classmethod
    def from_section(cls, s: Mapping[str, Any]) -> "IntercityPrivateParams":
        return cls(base_vnd=_vnd(s, "base_vnd", 50000, 300000, 1000), per_km_vnd=_vnd(s, "per_km_vnd", 4000, 15000),
                   commission=_rate(s, "commission_rate", "0.10", "0.25"), step=_step(s))


@dataclass(frozen=True)
class IntercityPoolParams:
    commission_seat: Fraction
    commission_topup: Fraction
    min_seats_ref: int
    allowed_driver_min_seats: tuple[int, ...]
    seat_band: tuple[Fraction, Fraction]
    door_surcharge_per_km_vnd: int
    max_corridor_deviation_km: Fraction
    step: int

    @classmethod
    def from_section(cls, s: Mapping[str, Any], private: IntercityPrivateParams) -> "IntercityPoolParams":
        band = (q(s["seat_price_band"][0]), q(s["seat_price_band"][1]))
        p = cls(commission_seat=_rate(s, "commission_seat", "0.05", "0.20"),
                commission_topup=q(s["commission_topup"]), min_seats_ref=int(s["min_seats_ref"]),
                allowed_driver_min_seats=tuple(int(x) for x in s["allowed_driver_min_seats"]), seat_band=band,
                door_surcharge_per_km_vnd=_vnd(s, "door_surcharge_per_km_vnd", 0, 10000, 1000),
                max_corridor_deviation_km=_rate(s, "max_corridor_deviation_km", "3.0", "20.0"), step=_step(s))
        if p.commission_topup != private.commission:
            raise PricingConfigError("commission_topup must equal car_intercity_private.commission_rate (D-51)")
        if p.min_seats_ref != 3:
            raise PricingConfigError("min_seats_ref is locked to 3 (D-38, P2-01)")
        if not set(p.allowed_driver_min_seats) <= {2, 3} or not p.allowed_driver_min_seats:
            raise PricingConfigError("allowed_driver_min_seats must be a non-empty subset of {2, 3}")
        if not (q("0.80") <= band[0] <= 1 <= band[1] <= q("1.20")):
            raise PricingConfigError("seat_price_band must lie in [0.80, 1.20] around 1")
        return p


@dataclass(frozen=True)
class PricingParams:
    """All five tariffs of one pricing_version."""
    pricing_version: str
    pool_policy_version: str
    bike: BikeTariff
    car: CarUrbanParams
    intercity_private: IntercityPrivateParams
    intercity_pool: IntercityPoolParams

    @classmethod
    def from_sections(cls, pricing_version: str, pool_policy_version: str,
                      sections: Mapping[str, Mapping[str, Any]]) -> "PricingParams":
        ip = IntercityPrivateParams.from_section(sections["car_intercity_private"])
        return cls(pricing_version=pricing_version, pool_policy_version=pool_policy_version,
                   bike=BikeTariff.from_section(sections["bike_urban"]),
                   car=CarUrbanParams.from_section(sections["car_urban"]), intercity_private=ip,
                   intercity_pool=IntercityPoolParams.from_section(sections["car_intercity_pool"], ip))


@dataclass(frozen=True)
class CancellationParams:
    """`cancellation_policy` (Section 18.7, D-52) of the locked baseline."""
    urban_free_cancel_grace_s: int
    urban_no_show_wait_min: int
    urban_single_rate: Fraction
    urban_single_cap_vnd: int
    urban_pool_rate_on_quote: Fraction
    intercity_private_free_lead_h: Fraction
    intercity_private_late_rate: Fraction
    intercity_pool_free_before_h: int
    intercity_pool_rate_72_24: Fraction
    intercity_pool_rate_after_24: Fraction
    merge_free_window_h: int
    pickup_order_fix_h: int

    @classmethod
    def from_baseline(cls, baseline: Mapping[str, Any]) -> "CancellationParams":
        c = baseline["cancellation_policy"]
        pool = baseline["car_intercity_pool"]
        p = cls(urban_free_cancel_grace_s=int(c["urban_free_cancel_grace_s"]),
                urban_no_show_wait_min=int(c["urban_no_show_wait_min"]),
                urban_single_rate=_rate(c, "urban_single_cancel_fee_rate", "0.10", "0.30"),
                urban_single_cap_vnd=_vnd(c, "urban_single_cancel_fee_cap_vnd", 0),
                urban_pool_rate_on_quote=_rate(c, "urban_pool_cancel_fee_rate_on_quote", "0.10", "0.30"),
                intercity_private_free_lead_h=q(c["intercity_private_free_cancel_lead_h"]),
                intercity_private_late_rate=q(c["intercity_private_late_cancel_fee_rate"]),
                intercity_pool_free_before_h=int(c["intercity_pool_free_cancel_before_h"]),
                intercity_pool_rate_72_24=_rate(c, "intercity_pool_cancel_fee_rate_72h_to_24h", "0.30", "0.70"),
                intercity_pool_rate_after_24=_rate(c, "intercity_pool_cancel_fee_rate_after_24h", "0.80", "1.00"),
                merge_free_window_h=int(pool["merge_confirmation_window_hours"]),
                pickup_order_fix_h=int(pool["pickup_order_fix_hours"]))
        if not 60 <= p.urban_free_cancel_grace_s <= 300:
            raise PricingConfigError("urban_free_cancel_grace_s outside [60, 300]")
        if p.intercity_pool_free_before_h != int(pool["booking_close_hours"]):
            raise PricingConfigError("intercity_pool_free_cancel_before_h must equal booking_close_hours (T-72h)")
        return p
