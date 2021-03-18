import brownie
from helpers import showBalances
from brownie import Contract
import time

def test_profitable_harvest(
    gov,
    vault,
    strategy,
    token,
    amount,
    weth_amount,
    yveCrv,
    weth,
    usdc,
    crv3,
    chain,
    whale_3crv,
    user
):
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount

    showBalances(token, vault, strategy, yveCrv, weth, usdc, crv3)

    strategy.harvest()
    assert token.balanceOf(strategy.address) == amount

    # showBalances(token, vault, strategy, yveCrv, weth, usdc, crv3)

    # Simulate a claim by sending some 3Crv to the strategy before harvest
    crv3.transfer(strategy, 10e20, {"from": whale_3crv})
    strategy.harvest()
    print("\n\n~~After Harvest #2~~")
    showBalances(token, vault, strategy, yveCrv, weth, usdc, crv3)
    assert token.balanceOf(strategy.address) > amount