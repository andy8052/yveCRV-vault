import brownie
from helpers import showBalances
from brownie import Contract
import time


def test_operation(accounts, token, vault, strategy, strategist, amount, user, crv3, chain, whale_3crv, gov):
    chain.snapshot()
    vault_before = token.balanceOf(vault)
    # Deposit to the vault
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount + vault_before

    # Move funds to strat
    strategy.harvest({"from":strategist})
    assert token.balanceOf(strategy.address) == amount + vault_before

    # Done to fix the UniswapV2: K issue
    pairs = [strategy.ethCrvPair(), strategy.ethYveCrvPair(), strategy.ethUsdcPair()]
    for pair in pairs:
        Contract.from_explorer(pair, owner=strategist).sync()

    # harvest
    crv3.transfer(strategy, 10e20, {"from": whale_3crv})
    strategy.harvest({"from":strategist})
    # withdrawal
    vault.withdraw({"from": user})
    assert token.balanceOf(user) != 0
    strategy.setBuffer(40, {"from": gov}) # increase buffer to 4%
    strategy.restoreApprovals({"from":gov}) # make sure reset approvals works
    chain.revert()