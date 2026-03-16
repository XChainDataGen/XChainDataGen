import argparse

from cli import Cli


def test_extract_data():
    args = argparse.Namespace(
        blockchains=["ethereum", "polygon"],
        bridge="polygon",
        start_ts=1735689600,  # 1st Jan 2025
        end_ts=1735776000,  # 2nd Jan 2025
    )

    Cli.extract_data(args)

    from repository.database import DBSession
    from repository.polygon.repository import (
        PolygonChildTokenBurnRepository,
        PolygonLockedTokenRepository,
        PolygonNewDepositBlockRepository,
        PolygonStateCommittedRepository,
        PolygonStateSyncedRepository,
    )

    polygon_deposit_requested = PolygonLockedTokenRepository(DBSession)
    events = polygon_deposit_requested.get_all()
    print(f"Number of events in PolygonLockedToken: {len(events)}")
    assert len(events) == 144, "Expected 144 events in PolygonLockedToken table after extraction."

    polygon_state_synced = PolygonStateSyncedRepository(DBSession)
    events = polygon_state_synced.get_all()
    print(f"Number of events in PolygonStateSynced: {len(events)}")
    assert len(events) == 245, "Expected 245 events in PolygonStateSynced table after extraction."

    polygon_state_committed = PolygonStateCommittedRepository(DBSession)
    events = polygon_state_committed.get_all()
    print(f"Number of events in PolygonStateCommitted: {len(events)}")
    assert (
        len(events) == 253
    ), "Expected 253 events in PolygonStateCommitted table after extraction."

    polygon_new_deposit_block = PolygonNewDepositBlockRepository(DBSession)
    events = polygon_new_deposit_block.get_all()
    print(f"Number of events in PolygonNewDepositBlock: {len(events)}")
    assert len(events) == 16, "Expected 16 events in PolygonNewDepositBlock table after extraction."

    polygon_child_token_burn = PolygonChildTokenBurnRepository(DBSession)
    events = polygon_child_token_burn.get_all()
    print(f"Number of events in PolygonChildTokenBurn: {len(events)}")
    assert (
        len(events) == 112
    ), "Expected 112 events in PolygonChildTokenBurn table after extraction."

    args = argparse.Namespace(
        bridge="polygon",
    )
    Cli.generate_data(args)

    from repository.database import DBSession
    from repository.polygon.repository import (
        PolygonCrossChainTransactionsRepository,
        PolygonPlasmaCrossChainTransactionsRepository,
    )

    polygon_cross_chain_transactions_repo = PolygonCrossChainTransactionsRepository(DBSession)
    transactions = polygon_cross_chain_transactions_repo.get_all()
    print(f"Number of transactions in PolygonCrossChainTransactions: {len(transactions)}")
    assert (
        len(transactions) == 274
    ), "Expected 153 events in PolygonCrossChainTransactions table after extraction."

    polygon_plasma_cross_chain_transactions_repo = PolygonPlasmaCrossChainTransactionsRepository(
        DBSession
    )
    plasma_transactions = polygon_plasma_cross_chain_transactions_repo.get_all()
    print(
        f"Number of transactions in PolygonPlasmaCrossChainTransactions: {len(plasma_transactions)}"
    )
    assert (
        len(plasma_transactions) == 19
    ), "Expected 19 events in PolygonPlasmaCrossChainTransactions table after extraction."
