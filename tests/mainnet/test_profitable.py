from ..helpers import showBalances
from brownie import Contract

def test_profitable_harvest(
    vault,
    strategy,
    strategist,
    token,
    amount,
    yveCrv,
    weth,
    usdc,
    crv3,
    chain,
    whale_3crv,
    user
):
    vault_before = token.balanceOf(vault)
    strat_before = token.balanceOf(strategy)
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    vault_after = token.balanceOf(vault)

    showBalances(token, vault, strategy, yveCrv, weth, usdc, crv3)

    strategy.harvest({"from": strategist})

    assert token.balanceOf(strategy.address) == amount + vault_before + strat_before

    # showBalances(token, vault, strategy, yveCrv, weth, usdc, crv3)
    # Done to fix the UniswapV2: K issue
    pairs = [strategy.ethCrvPair(), strategy.ethYvBoostPair(), strategy.ethUsdcPair()]
    for pair in pairs:
        Contract.from_explorer(pair, owner=strategist).sync()

    # Simulate a claim by sending some 3Crv to the strategy before harvest
    crv3.transfer(strategy, 1e22, {"from": whale_3crv})
    before = token.balanceOf(strategy.address) + token.balanceOf(vault.address)
    pps_before = vault.pricePerShare()
    strategy.harvest({"from": strategist})
    chain.sleep(60*60*6) # sleep to increase pps
    chain.mine(1)
    print("pps before",pps_before)
    print("pps after",vault.pricePerShare())
    assert vault.pricePerShare() > pps_before
    chain.mine(1)
    after = token.balanceOf(strategy.address) + token.balanceOf(vault.address)
    showBalances(token, vault, strategy, yveCrv, weth, usdc, crv3)
    print("before",before)
    print("after",after)
    assert after > before