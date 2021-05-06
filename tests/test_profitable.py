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
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount

    showBalances(token, vault, strategy, yveCrv, weth, usdc, crv3)

    strategy.harvest()
    assert token.balanceOf(strategy.address) == amount
    

    # showBalances(token, vault, strategy, yveCrv, weth, usdc, crv3)
    # Done to fix the UniswapV2: K issue
    pairs = [strategy.ethCrvPair(), strategy.ethYvBoostPair(), strategy.ethUsdcPair()]
    for pair in pairs:
        Contract.from_explorer(pair, owner=strategist).sync()

    
    # Simulate a claim by sending some 3Crv to the strategy before harvest
    crv3.transfer(strategy, 1e20, {"from": whale_3crv})
    
    assert False
    pps_before = vault.pricePerShare()
    print("pps_before: ",pps_before)
    strategy.harvest()
    chain.sleep(60*60*6) # sleep to increase pps
    chain.mine(1)
    print("pps_after: ",vault.pricePerShare())
    showBalances(token, vault, strategy, yveCrv, weth, usdc, crv3)
    assert token.balanceOf(strategy.address) > amount
    assert vault.pricePerShare() > pps_before