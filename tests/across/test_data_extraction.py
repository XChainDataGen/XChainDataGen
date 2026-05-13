import argparse

from cli import Cli


def test_extract_data():
    args = argparse.Namespace(
        blockchains=["ethereum", "arbitrum", "polygon", "optimism", "base", "scroll", "linea"],
        bridge="across",
        start_ts=1764547200,  # 1st Dec 2025 00:00
        end_ts=1764550800,  # 1st Dec 2025 01:00
    )

    Cli.extract_data(args)

    # now we can check if the data was extracted correctly
    # For example, we can check if the AcrossFundsDeposited table has been populated
    from repository.across.repository import (
        AcrossFilledRelayRepository,
        AcrossFundsDepositedRepository,
        AcrossRelayerRefundRepository,
    )
    from repository.database import DBSession

    across_funds_deposited = AcrossFundsDepositedRepository(DBSession)
    across_filled_relay_repo = AcrossFilledRelayRepository(DBSession)
    across_relayer_refund_repo = AcrossRelayerRefundRepository(DBSession)

    events = across_funds_deposited.get_all()
    print(f"Number of events in AcrossFundsDeposited: {len(events)}")
    assert len(events) == 447, (
        "Expected 447 events in AcrossFundsDepositedRepository table after extraction."
    )

    events = across_filled_relay_repo.get_all()
    print(f"Number of events in AcrossFilledRelay: {len(events)}")
    assert len(events) == 446, (
        "Expected 446 events in AcrossFilledRelayRepository table after extraction."
    )

    events = across_relayer_refund_repo.get_all()
    print(f"Number of events in AcrossRelayerRefund: {len(events)}")
    assert len(events) == 128, (
        "Expected 128 events in AcrossRelayerRefundRepository table after extraction."
    )

    args = argparse.Namespace(
        bridge="across",
    )
    Cli.generate_data(args)

    # Here we can check if the data was generated correctly
    from repository.across.repository import AcrossCrossChainTransactionRepository
    from repository.database import DBSession

    across_cross_chain_transactions_repo = AcrossCrossChainTransactionRepository(DBSession)
    transactions = across_cross_chain_transactions_repo.get_all()

    print(f"Number of transactions in AcrossCrossChainTransaction: {len(transactions)}")
    assert len(transactions) == 445, (
        "Expected 445 events in AcrossCrossChainTransaction table after extraction."
    )
