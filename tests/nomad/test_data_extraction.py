import argparse

from cli import Cli


def test_extract_data():
    args = argparse.Namespace(
        blockchains=["ethereum", "moonbeam"],
        bridge="nomad",
        start_ts=1654041600,  # 1st Jun 2022
        end_ts=1654128000,    # 2nd Jun 2022
    )

    Cli.extract_data(args)

    from repository.database import DBSession
    from repository.nomad.repository import (
        NomadEthHelperSendRepository,
        NomadHomeDispatchRepository,
        NomadReplicaProcessRepository,
        NomadRouterReceiveRepository,
        NomadRouterSendRepository,
    )

    nomad_router_send = NomadRouterSendRepository(DBSession)
    events = nomad_router_send.get_all()
    print(f"Number of events in NomadRouterSend: {len(events)}")
    assert len(events) == 109, "Expected events in NomadRouterSend table after extraction."

    nomad_router_receive = NomadRouterReceiveRepository(DBSession)
    events = nomad_router_receive.get_all()
    print(f"Number of events in NomadRouterReceive: {len(events)}")
    assert len(events) == 337, "Expected events in NomadRouterReceive table after extraction."

    nomad_eth_helper_send = NomadEthHelperSendRepository(DBSession)
    events = nomad_eth_helper_send.get_all()
    print(f"Number of events in NomadEthHelperSend: {len(events)}")
    assert len(events) == 36, "Expected events in NomadEthHelperSend table after extraction."

    nomad_replica_process = NomadReplicaProcessRepository(DBSession)
    events = nomad_replica_process.get_all()
    print(f"Number of events in NomadReplicaProcess: {len(events)}")
    assert len(events) == 57, "Expected events in NomadReplicaProcess table after extraction."

    nomad_home_dispatch = NomadHomeDispatchRepository(DBSession)
    events = nomad_home_dispatch.get_all()
    print(f"Number of events in NomadHomeDispatch: {len(events)}")
    assert len(events) == 109, "Expected events in NomadHomeDispatch table after extraction."

    args = argparse.Namespace(
        bridge="nomad",
    )
    Cli.generate_data(args)

    # Here we can check if the data was generated correctly
    from repository.database import DBSession
    from repository.nomad.repository import NomadCrossChainTransactionRepository

    nomad_cctx_repo = NomadCrossChainTransactionRepository(DBSession)
    transactions = nomad_cctx_repo.get_all()
    print(f"Number of transactions in NomadCrossChainTransactions: {len(transactions)}")
    assert len(transactions) == 55, (
        "Expected transactions in NomadCrossChainTransactions table after generation."
    )