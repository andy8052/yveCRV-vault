import brownie
from helpers import showBalances
from brownie import Contract
import time

def test_swap_over_mint(
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
    crv,
    chain,
    whale_3crv,
    whale_eth,
    sushiswap,
    yveCrvContract,
    user
):
    chain.snapshot()
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})

    # showBalances(token, vault, strategy, yveCrv, weth, usdc, crv3)

    # Move deposited funds to vault
    strategy.harvest()

    # showBalances(token, vault, strategy, yveCrv, weth, usdc, crv3)

    # Simulate a claim by sending some 3Crv to the strategy before harvest
    crv3.transfer(strategy, 10e21, {"from": whale_3crv})

    pairs = [strategy.ethCrvPair(), strategy.ethYveCrvPair(), strategy.ethUsdcPair()]
    for pair in pairs:
        Contract.from_explorer(pair, owner=strategist).sync()

    # Swap a load of ETH for CRV to make CRV more expensive than yveCRV
    before_shares = yveCrvContract.totalSupply()
    sushiswap.swapExactETHForTokens(
        0,
        [weth.address, crv.address],
        whale_eth,
        time.time()+500,
        {"from": whale_eth, "value": 1e21},
    )
    strategy.harvest()
    after_shares = yveCrvContract.totalSupply()

    # showBalances(token, vault, strategy, yveCrv, weth, usdc, crv3)
    assert after_shares == before_shares  # Ensure that we didn't mint
    chain.revert()

def test_mint_over_swap(
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
    whale_eth,
    sushiswap,
    yveCrvContract,
    crv,
    user
):
    chain.snapshot()
    pairs = [strategy.ethCrvPair(), strategy.ethYveCrvPair(), strategy.ethUsdcPair()]
    for pair in pairs:
        Contract.from_explorer(pair, owner=strategist).sync()
    # Deposit to the vault and harvest
    # print(yveCrv.strategies(strategy)) # Strategy params (perf fee, activation, debtraatio, mindebtperharvest, maxdebtperharvest, lastreport, totaldebt)
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})

    showBalances(token, vault, strategy, yveCrv, weth, usdc, crv3)

    # Move deposited funds to vault
    strategy.harvest()

    showBalances(token, vault, strategy, yveCrv, weth, usdc, crv3)

    # Simulate a claim by sending some 3Crv to the strategy before harvest
    crv3.transfer(strategy, 10e21, {"from": whale_3crv})

    # Swap a load of ETH for yveCRV to make yveCRV more expensive than CRV
    sushiswap.swapExactETHForTokens(
        0,
        [weth.address, token.address],
        whale_eth,
        time.time()+10,
        {"from": whale_eth, "value": 1e22},
    )
    before_shares = yveCrvContract.totalSupply()

    strategy.harvest()
    after_shares = yveCrvContract.totalSupply()

    # showBalances(token, vault, strategy, yveCrv, weth, usdc, crv3)
    assert after_shares > before_shares  # Ensure that we didn't mint
