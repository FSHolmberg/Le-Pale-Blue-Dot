

from src.agents.bukowski_ledger import BukowskiLedger, LedgerEntry

def test_bukowski_logs_and_returns_last_entries():
    ledger = BukowskiLedger()

    ledger.log(LedgerEntry("u", "user", "1", 1.0))
    ledger.log(LedgerEntry("u", "user", "2", 2.0))
    ledger.log(LedgerEntry("u", "user", "3", 3.0))

    last_two = ledger.get_last(2)

    assert [e.text for e in last_two] == ["2", "3"]


def test_bukowski_handles_small_n():
    ledger = BukowskiLedger()

    ledger.log(LedgerEntry("u", "user", "only", 0.0))

    assert [e.text for e in ledger.get_last()] == ["only"]
    assert ledger.get_last() == []
