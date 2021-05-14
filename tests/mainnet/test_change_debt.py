import brownie
from helpers import showBalances
from brownie import Contract
import time

def test_change_debt(gov, token, vault, strategy, strategist, amount, user):
    # Deposit to the vault and harvest
    vault_before = token.balanceOf(vault)
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    strategy.harvest()
    vault.updateStrategyDebtRatio(strategy.address, 5_000, {"from": gov})
    strategy.harvest({"from":strategist})
    highRange = (amount + vault_before) / 2 + 1e10
    lowRange = (amount + vault_before) / 2 - 1e10
    assert token.balanceOf(strategy.address) < highRange
    assert token.balanceOf(strategy.address) > lowRange

    vault.updateStrategyDebtRatio(strategy.address, 10_000, {"from": gov})
    strategy.harvest({"from":strategist})
    assert token.balanceOf(strategy.address) == amount + vault_before