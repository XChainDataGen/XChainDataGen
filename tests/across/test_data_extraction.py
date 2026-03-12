import argparse

from cli import Cli


def test_extract_data():
    args = argparse.Namespace(
        blockchains=["ethereum", "arbitrum", "polygon", "optimism", "base", "scroll", "linea"],
        bridge="across",
        start_ts=1733011200,  # 1st Dec 2024 00:00
        end_ts=1733014800,  # 1st Dec 2024 01:00
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
    assert len(events) == 911, (
        "Expected 911 events in AcrossFundsDepositedRepository table after extraction."
    )

    events = across_filled_relay_repo.get_all()
    print(f"Number of events in AcrossFilledRelay: {len(events)}")
    assert len(events) == 912, (
        "Expected 912 events in AcrossFilledRelayRepository table after extraction."
    )

    events = across_relayer_refund_repo.get_all()
    print(f"Number of events in AcrossRelayerRefund: {len(events)}")
    assert len(events) == 93, (
        "Expected 93 events in AcrossRelayerRefundRepository table after extraction."
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
    assert len(transactions) == 900, (
        "Expected 900 events in AcrossCrossChainTransaction table after extraction."
    )
