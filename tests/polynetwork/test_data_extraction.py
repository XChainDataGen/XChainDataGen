import argparse

from cli import Cli


def test_extract_data():
    args = argparse.Namespace(
        blockchains=["ethereum", "bnb", "polygon", "arbitrum"],
        bridge="polynetwork",
        start_ts=1688230800,  # 1st July 2022 17:00:00 UTC
        end_ts=1688256000,    # 2nd July 2022 00:00:00 UTC
    )

    Cli.extract_data(args)

    from repository.database import DBSession
    from repository.polynetwork.repository import (
        PolynetworkCrossChainEventRepository,
        PolynetworkLockEventRepository,
        PolynetworkUnlockEventRepository,
        PolynetworkVerifyHeaderAndExecuteTxEventRepository,
    )

    polynetwork_cross_chain_event = PolynetworkCrossChainEventRepository(DBSession)
    events = polynetwork_cross_chain_event.get_all()
    print(f"Number of events in PolynetworkCrossChainEvent: {len(events)}")
    assert len(events) == 389, "Expected events in PolynetworkCrossChainEvent table" \
        + "after extraction."

    polynetwork_lock_event = PolynetworkLockEventRepository(DBSession)
    events = polynetwork_lock_event.get_all()
    print(f"Number of events in PolynetworkLockEvent: {len(events)}")
    assert len(events) == 389, "Expected events in PolynetworkLockEvent table after extraction."

    polynetwork_unlock_event = PolynetworkUnlockEventRepository(DBSession)
    events = polynetwork_unlock_event.get_all()
    print(f"Number of events in PolynetworkUnlockEvent: {len(events)}")
    assert len(events) == 132, "Expected events in PolynetworkUnlockEvent table after extraction."

    polynetwork_verify_header_event = PolynetworkVerifyHeaderAndExecuteTxEventRepository(DBSession)
    events = polynetwork_verify_header_event.get_all()
    print(f"Number of events in PolynetworkVerifyHeaderAndExecuteTxEvent: {len(events)}")
    assert len(events) == 132, "Expected events in PolynetworkVerifyHeaderAndExecuteTxEvent table" \
        + "after extraction."

    args = argparse.Namespace(
        bridge="polynetwork",
    )
    Cli.generate_data(args)

    # Here we can check if the data was generated correctly
    from repository.database import DBSession
    from repository.polynetwork.repository import PolynetworkCrossChainTransactionsRepository

    polynetwork_cctx_repo = PolynetworkCrossChainTransactionsRepository(DBSession)
    transactions = polynetwork_cctx_repo.get_all()
    print(f"Number of transactions in PolynetworkCrossChainTransactions: {len(transactions)}")
    assert len(transactions) == 119, (
        "Expected transactions in PolynetworkCrossChainTransactions table after generation."
    )