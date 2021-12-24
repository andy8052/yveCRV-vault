import brownie
from brownie import Contract
import time

def test_yswap(
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
    user,
    trade_factory,
    sushi_swapper,
    ymechs_safe
):
    vault_before = token.balanceOf(vault)
    strat_before = token.balanceOf(strategy)
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    vault_after = token.balanceOf(vault)

    strategy.harvest({"from": strategist})


    # Simulate a claim by sending some 3Crv to the strategy before harvest
    crv3.transfer(strategy, Wei("100 ether"), {"from": whale_3crv})
    strategy.harvest({"from": strategist})
    chain.sleep(60*60*6) # sleep to increase pps
    chain.mine(1)

    print(f"Executing trades...")
    for id in trade_factory.pendingTradesIds(strategy):
        trade = trade_factory.pendingTradesById(id).dict()
        token_in = trade["_tokenIn"]
        token_out = trade["_tokenOut"]
        print(f"Executing trade {id}, tokenIn: {token_in} -> tokenOut {token_out}")


        path = [toke_token.address, token.address]
        trade_data = encode_abi(["address[]"], [path])
        trade_factory.execute["uint256, address, uint, bytes"](id, sushi_swapper.address, Wei("0.1 ether"), trade_data, {"from": ymechs_safe})
