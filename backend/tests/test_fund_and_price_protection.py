"""P3.4 / P3.5 on the throwaway database: fund ledger and driver payouts (append-only, balance chain,
signs, one entry per booking and type, insufficient fund, idempotent settlement, G12 reconciliation)
and the database guards of the price protection (frozen participant, locked pool booking, stale plan
version). Pricing parameters come from the seeded `pricing_configs` rows. Data is SYNTHETIC."""

import uuid
from datetime import UTC, datetime, timedelta
from fractions import Fraction

import pytest
import yaml
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from app.modules.fund import service as fund
from app.modules.pooling import pricing_state
from app.modules.pricing import pool, service as pricing_service, settlement
from app.modules.pricing.cancellation import CancelContext, cancellation_fee
from app.modules.pricing.params import CancellationParams
from tests import p2_fixtures as fx
from tests.conftest import CONFIG_BASELINE

pytestmark = pytest.mark.db
NOW = datetime(2026, 11, 4, 8, 0, tzinfo=UTC)
BASELINE = yaml.safe_load(CONFIG_BASELINE.read_text(encoding="utf-8"))
VERSION = BASELINE["pricing_version"]
POLICY = BASELINE["pool_policy_version"]


@pytest.fixture()
def world(db_session: Session) -> Session:
    fx.setup_reference_data(db_session)
    return db_session


def booking(s: Session, service: str, *, price_status: str, final: int | None, cause: str = "NONE",
            driver: uuid.UUID | None = None, cap: int | None = None, ride_status: str = "COMPLETED",
            plan: uuid.UUID | None = None) -> tuple[uuid.UUID, uuid.UUID]:
    if driver is None:
        driver, _ = fx.driver(s, 105.8, 21.0, NOW, pool=True)
    rider = fx.user(s)
    trip = fx.trip(s, rider, (105.80, 21.00), (105.85, 21.03), NOW, allowed=[service])
    b = uuid.uuid4()
    s.execute(text("INSERT INTO bookings (id, request_id, user_id, driver_id, service_code, booking_type, seat_count, "
                   "ride_plan_id, ride_status, price_status, quoted_price_cap_vnd, final_price_vnd, unmatched_cause, "
                   "pricing_version) VALUES (:b, :t, :u, :d, :s, 'NOW', 1, :p, :rs, :ps, :cap, :f, :c, :v)"),
              {"b": b, "t": trip, "u": rider, "d": driver, "s": service, "p": plan, "rs": ride_status, "ps": price_status,
               "cap": cap if cap is not None else final, "f": final, "c": cause, "v": VERSION})
    return b, driver


def pool_plan(s: Session, driver: uuid.UUID, vehicle: uuid.UUID) -> uuid.UUID:
    p = uuid.uuid4()
    s.execute(text("INSERT INTO ride_plans (id, driver_id, vehicle_id, service_code, status, plan_version, "
                   "pricing_version) VALUES (:p, :d, :v, 'CAR_URBAN_POOL', 'PLAN_OPEN_SEARCHING', 1, :pv)"),
              {"p": p, "d": driver, "v": vehicle, "pv": VERSION})
    return p


def participant(s: Session, plan: uuid.UUID, b: uuid.UUID, P: int) -> None:
    s.execute(text("INSERT INTO ride_participants (ride_plan_id, booking_id, seat_count, private_fare_vnd, "
                   "direct_distance_m, direct_duration_s) VALUES (:p, :b, 1, :pf, 14000, 2400)"),
              {"p": plan, "b": b, "pf": P})


def test_load_pricing_reads_the_immutable_rows(world: Session) -> None:
    p = pricing_service.load_pricing(world, VERSION)
    assert p.pricing_version == VERSION and p.pool_policy_version == POLICY
    assert p.car.base_vnd == 20000 and p.bike.per_km_vnd == 4500 and p.intercity_private.base_vnd == 150000
    with pytest.raises(DBAPIError):  # pricing_configs rows can never be changed (Baseline 5.1)
        world.execute(text("UPDATE pricing_configs SET params_json = '{}' WHERE version = :v"), {"v": VERSION})
    world.rollback()


def test_settlements_write_payout_and_fund_entries_and_reconcile(world: Session) -> None:
    s = world
    params = pricing_service.load_pricing(s, VERSION)
    seed = fund.seed_fund(s, BASELINE)
    assert seed.amount_signed_vnd == seed.balance_after_vnd == 5_000_000
    assert fund.seed_fund(s, BASELINE).id == seed.id                                   # once
    car, vehicle = fx.driver(s, 105.8, 21.0, NOW, pool=True)
    plan = pool_plan(s, car, vehicle)
    a, _ = booking(s, "CAR_URBAN_POOL", price_status="MATCHED_LOCKED", final=143000, driver=car, cap=174000, plan=plan)
    b, _ = booking(s, "CAR_URBAN_POOL", price_status="MATCHED_LOCKED", final=105000, driver=car, cap=119000, plan=plan)
    u, _ = booking(s, "CAR_URBAN_POOL", price_status="UNMATCHED_LOCKED", final=174000, cause="NO_COMPATIBLE",
                   driver=car, cap=174000, plan=plan)
    d, _ = booking(s, "CAR_URBAN_POOL", price_status="UNMATCHED_LOCKED", final=155000, cause="DRIVER_DECLINED",
                   driver=car, cap=174000, plan=plan)
    for bk, P in ((a, 194000), (b, 133000), (u, 194000), (d, 194000)):
        participant(s, plan, bk, P)
    f, _ = booking(s, "BIKE_URBAN", price_status="FIXED_LOCKED", final=81000)
    s.commit()
    for bk in (a, b, u, d, f):
        bs = fund.settlement_for_completed_booking(s, params, bk)
        fund.record_settlement(s, booking_id=bk, driver_id=bs.booking.driver_id, settlement=bs.settlement,
                               pricing_version=VERSION, pool_policy_version=POLICY, ride_plan_id=bs.ride_plan_id)
    rows = {r.booking_id: r for r in s.execute(text("SELECT * FROM driver_payouts")).mappings()}
    assert (rows[a]["driver_base_amount_vnd"], rows[a]["platform_net_amount_vnd"], rows[a]["fund_contribution_vnd"]) == \
        (121550, 17160, 4290)
    assert (rows[u]["guarantee_amount_vnd"], rows[u]["total_driver_payout_vnd"]) == (7300, 155200)
    assert (rows[d]["guarantee_amount_vnd"], rows[d]["total_driver_payout_vnd"]) == (0, 131750)
    assert rows[f]["driver_base_amount_vnd"] == 64800 and rows[a]["pricing_version"] == VERSION
    assert fund.balance(s) == 5_000_000 + 4290 + 3150 - 7300
    ledger = s.execute(text("SELECT entry_type, booking_id, amount_signed_vnd, pricing_version, ride_plan_id "
                            "FROM fund_ledger WHERE booking_id IS NOT NULL ORDER BY id")).all()
    assert [(e[0], e[2]) for e in ledger] == [("CONTRIBUTION", 4290), ("CONTRIBUTION", 3150), ("GUARANTEE_PAYOUT", -7300)]
    assert all(e[3] == VERSION and e[4] == plan for e in ledger)                       # traceable
    # idempotent: same numbers -> no new row, different numbers -> refused
    bs = fund.settlement_for_completed_booking(s, params, a)
    fund.record_settlement(s, booking_id=a, driver_id=car, settlement=bs.settlement, pricing_version=VERSION,
                           pool_policy_version=POLICY)
    assert s.execute(text("SELECT count(*) FROM fund_ledger")).scalar_one() == 4
    other = settlement.settle_pool_matched(params, 142000)
    with pytest.raises(fund.SettlementConflict):
        fund.record_settlement(s, booking_id=a, driver_id=car, settlement=other, pricing_version=VERSION,
                               pool_policy_version=POLICY)
    rep = fund.reconcile(s)
    assert rep.ok and rep.balance == rep.sum_of_amounts == fund.ledger_total(s)       # G12: 0 VND difference


def test_cancellation_fee_flows_to_the_fund(world: Session) -> None:
    s = world
    params = pricing_service.load_pricing(s, VERSION)
    fund.seed_fund(s, BASELINE)
    c, car = booking(s, "CAR_URBAN_POOL", price_status="POOL_SEARCHING", final=None, cap=174000,
                     ride_status="CANCELLED_BY_PASSENGER")
    s.commit()
    out = cancellation_fee(params, CancellationParams.from_baseline(BASELINE), CancelContext(
        service_code="CAR_URBAN_POOL", actor="PASSENGER", kind="CANCEL", at=NOW, deposited_vnd=174000,
        confirmed_at=NOW - timedelta(minutes=5), quote=155000, vehicle_has_other_riders=True))
    fund.record_settlement(s, booking_id=c, driver_id=car, settlement=fund.cancellation_settlement(out),
                           pricing_version=VERSION, pool_policy_version=POLICY)
    assert fund.balance(s) == 5_000_000 + 15500
    assert s.execute(text("SELECT entry_type FROM fund_ledger ORDER BY id DESC LIMIT 1")).scalar_one() == \
        "CANCEL_FEE_INFLOW"
    assert fund.reconcile(s).ok


def test_ledger_is_append_only_and_chained(world: Session) -> None:
    s = world
    seed = fund.seed_fund(s, BASELINE)
    for sql in ("UPDATE fund_ledger SET amount_signed_vnd = 1 WHERE id = :i", "DELETE FROM fund_ledger WHERE id = :i"):
        with pytest.raises(DBAPIError):
            s.execute(text(sql), {"i": seed.id})
        s.rollback()
    b, _ = booking(s, "CAR_URBAN_POOL", price_status="MATCHED_LOCKED", final=143000, cap=174000)
    s.commit()
    with pytest.raises(DBAPIError):  # a forged balance breaks the chain
        s.execute(text("INSERT INTO fund_ledger (entry_type, booking_id, amount_signed_vnd, balance_after_vnd, "
                       "pricing_version, pool_policy_version) VALUES ('CONTRIBUTION', :b, 4290, 9999999, :v, :p)"),
                  {"b": b, "v": VERSION, "p": POLICY})
    s.rollback()
    with pytest.raises(IntegrityError):  # wrong sign for the type
        fund.append_entry(s, "CONTRIBUTION", -10, booking_id=b, pricing_version=VERSION, pool_policy_version=POLICY)
    s.rollback()
    orphan = fund.append_entry(s, "CONTRIBUTION", 4290, booking_id=b, pricing_version=VERSION, pool_policy_version=POLICY)
    s.commit()
    with pytest.raises(IntegrityError):  # one entry per (booking, type)
        fund.append_entry(s, "CONTRIBUTION", 4290, booking_id=b, pricing_version=VERSION, pool_policy_version=POLICY)
    s.rollback()
    # Phase 9 may fill the transaction hash once, nothing else
    s.execute(text("UPDATE fund_ledger SET onchain_tx_hash = '0xabc' WHERE id = :i"), {"i": seed.id})
    s.commit()
    with pytest.raises(DBAPIError):
        s.execute(text("UPDATE fund_ledger SET onchain_tx_hash = '0xdef' WHERE id = :i"), {"i": seed.id})
    s.rollback()
    # an entry with no payout document behind it is flagged: no fund balance without a record (G12)
    rep = fund.reconcile(s)
    assert not rep.ok and rep.orphan_entries == [orphan.id] and rep.balance == rep.sum_of_amounts


def test_guarantee_never_drives_the_fund_negative(world: Session) -> None:
    s = world
    b, car = booking(s, "CAR_URBAN_POOL", price_status="UNMATCHED_LOCKED", final=174000, cause="NO_COMPATIBLE",
                     cap=174000)
    s.commit()
    params = pricing_service.load_pricing(s, VERSION)
    st = settlement.settle_pool_unmatched(params, 194000, 174000, "NO_COMPATIBLE")
    with pytest.raises(fund.FundInsufficient):        # not seeded: balance 0 cannot pay 7.300
        fund.record_settlement(s, booking_id=b, driver_id=car, settlement=st, pricing_version=VERSION,
                               pool_policy_version=POLICY)
    assert s.execute(text("SELECT count(*) FROM driver_payouts")).scalar_one() == 0   # nothing half-written
    assert s.execute(text("SELECT count(*) FROM fund_ledger")).scalar_one() == 0


def test_payouts_are_immutable_and_must_add_up(world: Session) -> None:
    s = world
    b, car = booking(s, "BIKE_URBAN", price_status="FIXED_LOCKED", final=81000)
    s.commit()
    with pytest.raises(IntegrityError):  # gross != base + platform + fund
        s.execute(text("INSERT INTO driver_payouts (booking_id, driver_id, gross_fare_charged_vnd, driver_base_amount_vnd, "
                       "total_driver_payout_vnd, platform_net_amount_vnd, payout_kind, pricing_version) VALUES "
                       "(:b, :d, 81000, 64800, 64800, 16000, 'FIXED', :v)"), {"b": b, "d": car, "v": VERSION})
    s.rollback()
    params = pricing_service.load_pricing(s, VERSION)
    fund.record_settlement(s, booking_id=b, driver_id=car, settlement=settlement.settle_fixed(params, "BIKE_URBAN", 81000),
                           pricing_version=VERSION, pool_policy_version=POLICY)
    with pytest.raises(DBAPIError):
        s.execute(text("UPDATE driver_payouts SET driver_base_amount_vnd = 70000 WHERE booking_id = :b"), {"b": b})
    s.rollback()


def test_frozen_participant_and_locked_booking_cannot_change(world: Session) -> None:
    s = world
    car, vehicle = fx.driver(s, 105.8, 21.0, NOW, pool=True)
    plan = pool_plan(s, car, vehicle)
    b, _ = booking(s, "CAR_URBAN_POOL", price_status="MATCHED_LOCKED", final=105000, driver=car, cap=119000,
                   ride_status="RIDE_STARTED", plan=plan)
    s.execute(text("INSERT INTO ride_participants (ride_plan_id, booking_id, seat_count, private_fare_vnd, cap_fare_vnd, "
                   "floor_fare_vnd, fare_exact_vnd, fare_charged_vnd, is_price_frozen) VALUES "
                   "(:p, :b, 1, 133000, 106400, 53200, 105195.74, 105000, true)"), {"p": plan, "b": b})
    s.commit()
    for sql in ("UPDATE ride_participants SET fare_charged_vnd = 104000 WHERE booking_id = :b",
                "UPDATE ride_participants SET is_price_frozen = false WHERE booking_id = :b",
                "UPDATE bookings SET final_price_vnd = 104000 WHERE id = :b",
                "UPDATE bookings SET price_status = 'POOL_SEARCHING' WHERE id = :b"):
        with pytest.raises(DBAPIError):
            s.execute(text(sql), {"b": b})
        s.rollback()
    # other fields of the same rows remain writable (e.g. the ride lifecycle of Phase 4)
    s.execute(text("UPDATE ride_participants SET traveled_km_before_last_replan = 3.5 WHERE booking_id = :b"), {"b": b})
    s.execute(text("UPDATE bookings SET ride_status = 'COMPLETED' WHERE id = :b"), {"b": b})
    s.commit()


def test_store_plan_pricing_refuses_a_stale_plan_version(world: Session) -> None:
    s = world
    car, vehicle = fx.driver(s, 105.8, 21.0, NOW, pool=True)
    plan = pool_plan(s, car, vehicle)
    a, _ = booking(s, "CAR_URBAN_POOL", price_status="POOL_SEARCHING", final=None, driver=car, cap=174000,
                   ride_status="RIDE_STARTED", plan=plan)
    b, _ = booking(s, "CAR_URBAN_POOL", price_status="POOL_SEARCHING", final=None, driver=car, cap=119000,
                   ride_status="CONFIRMED", plan=plan)
    participant(s, plan, a, 194000)
    participant(s, plan, b, 133000)
    s.commit()
    car_p = pricing_service.load_pricing(s, VERSION).car
    priced = pool.price_new_plan(car_p, [pool.PoolRider("A", 194000, 1, Fraction(2400), Fraction(1, 4)),
                                         pool.PoolRider("B", 133000, 1, Fraction(1680))], 17500, 52 * 60, 4)
    assert priced.ok
    v = pricing_state.store_plan_pricing(s, plan, 1, priced, {"A": a, "B": b})
    assert v == 2
    st = pricing_state.plan_pricing_states(s, [plan])[plan]
    assert st.plan_fare_exact == 248500 and st.plan_version == 2
    by = {x.booking_id: x for x in st.participants}
    assert by[a].fare_exact == priced.prices["A"].fare_exact and by[a].fare_charged == 143000
    assert sum(x.fare_exact for x in st.participants) == st.plan_fare_exact          # loss-free storage
    est = s.execute(text("SELECT current_estimated_price_vnd FROM bookings WHERE id = :b"), {"b": b}).scalar_one()
    assert est == 105000
    with pytest.raises(pricing_state.StalePlanVersion):                               # computed on version 1
        pricing_state.store_plan_pricing(s, plan, 1, priced, {"A": a, "B": b})
