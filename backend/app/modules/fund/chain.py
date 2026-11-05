"""Interface for the Phase 9 escrow synchronisation of the guarantee fund (Revision 9 Section 80.3).

Phase 3 only defines the boundary: `fund_ledger.onchain_tx_hash` stays NULL and no on-chain
transaction is simulated or assumed. Phase 9 implements `FundChainSync` with the escrow adapter,
submits each entry with its booking id, and records the transaction hash (the ledger trigger allows
that one column to be filled once)."""

import uuid
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class LedgerEvent:
    ledger_id: int
    entry_type: str                  # CONTRIBUTION | GUARANTEE_PAYOUT | CANCEL_FEE_INFLOW | INITIAL_SEED
    booking_id: uuid.UUID | None
    amount_signed_vnd: int           # 1 base unit = 1 VND (D-48)
    balance_after_vnd: int           # must equal guaranteeFundBalance after the transaction (G18)


class FundChainSync(Protocol):
    def submit(self, event: LedgerEvent) -> str:
        """Send the entry on chain; returns the transaction hash. Phase 9."""
        ...
