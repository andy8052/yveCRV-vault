import brownie
from helpers import showBalances
from brownie import Contract
import time

def test_profitable_harvest(
    gov,
    vault,
    strategy,
    strategist,
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
    vault_before = token.balanceOf(vault)
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    vault_after = token.balanceOf(vault)
    assert vault_after == amount + vault_before

    showBalances(token, vault, strategy, yveCrv, weth, usdc, crv3)

    strategy.harvest({"from": strategist})
    assert token.balanceOf(strategy.address) == vault_after

    # showBalances(token, vault, strategy, yveCrv, weth, usdc, crv3)
    # Done to fix the UniswapV2: K issue
    pairs = [strategy.ethCrvPair(), strategy.ethYveCrvPair(), strategy.ethUsdcPair()]
    for pair in pairs:
        Contract.from_explorer(pair, owner=strategist).sync()

    # Simulate a claim by sending some 3Crv to the strategy before harvest
    crv3.transfer(strategy, 1e18, {"from": whale_3crv})
    before = token.balanceOf(strategy.address) + token.balanceOf(vault.address)
    strategy.harvest({"from": strategist})
    chain.sleep(60*60*6) # sleep to increase pps
    chain.mine(1)
    after = token.balanceOf(strategy.address) + token.balanceOf(vault.address)
    print("\n\n~~After Harvest #2~~")
    showBalances(token, vault, strategy, yveCrv, weth, usdc, crv3)
    assert False
    assert after > before