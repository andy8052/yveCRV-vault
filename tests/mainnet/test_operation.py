import brownie, math, time
from helpers import showBalances
from brownie import Contract
import time


def test_operation(accounts, token, eth_whale, vault, strategy, strategist, amount, user, crv3, chain, whale_3crv, gov):
    chain.snapshot()
    vault_before = token.balanceOf(vault)
    strat_before = token.balanceOf(strategy)
    # Deposit to the vault
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount + vault_before

    # Move funds to strat
    tx= strategy.harvest({"from":strategist})
    print("-- Harvest no profit --")
    print(tx.events['Harvested'])
    chain.sleep(60*60*6) # sleep to increase pps
    chain.mine(1)
    assert token.balanceOf(strategy.address) == amount + vault_before + strat_before

    # Done to fix the UniswapV2: K issue
    pairs = [strategy.ethCrvPair(), strategy.ethYvBoostPair(), strategy.ethUsdcPair()]
    for pair in pairs:
        Contract(pair, owner=strategist).sync()

    # harvest to accrue strategist reward as this is part of our test
    # to make sure that these yvBOOST shares are separated from the purhcased
    # amount and not used to withdraw yveCRV from vault
    strategist_reward_before = vault.balanceOf(strategy)
    crv3.transfer(strategy, 10e20, {"from": whale_3crv})
    tx = strategy.harvest({"from":strategist})
    print()
    print("-- Harvest with profit --")
    print(tx.events['Harvested'])
    print(tx.events['Money'])
    print(tx.events['Test'])
    chain.sleep(60*60*6) # sleep to increase pps
    chain.mine(1)
    params = vault.strategies(strategy)
    total_debt = params.dict()["totalDebt"]
    assert total_debt == token.balanceOf(strategy)

    strategist_reward_before = vault.balanceOf(strategy)
    token.transfer(strategy, 10e20, {"from": user})
    print()
    print("-- Harvest with profit 2--")
    tx = strategy.harvest({"from":strategist})
    print(tx.events['Harvested'])
    print(tx.events['Money'])
    print(tx.events['Test'])
    chain.sleep(60*60*6) # sleep to increase pps
    chain.mine(1)

    params = vault.strategies(strategy)
    total_debt = params.dict()["totalDebt"]
    assert total_debt == token.balanceOf(strategy)

    # test strategist reward increase
    strategist_reward_after = vault.balanceOf(strategy)
    print("strategist reward before",strategist_reward_before)
    print("strategist reward after",strategist_reward_after)
    assert strategist_reward_after > strategist_reward_before

    # Test mint/buy paths
    crv3.transfer(strategy, 10e20, {"from": whale_3crv})
    chain.snapshot()
    a = accounts[7]
    a2 = accounts[8]
    a3 = accounts[9]
    a4 = accounts[6]
    a5 = accounts[5]
    a6 = accounts[3]
    a7 = accounts[2]
    sushi = Contract("0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F")
    pathBOOST = [
        "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",   # WETH
        "0x9d409a0a012cfba9b15f6d4b36ac57a46966ab9a"   # yvBOOST
    ]
    pathCRV = [
        "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",   # WETH
        "0xD533a949740bb3306d119CC777fa900bA034cd52"   # CRV
    ]
    sushi.swapExactETHForTokens(0,pathCRV,a,math.ceil(time.time()+1e6),{'from':a,'value':100e18})
    tx1 = strategy.harvest()
    assert tx1.events['BuyOrMint']['shouldMint'] == False

    chain.revert()

    # Make yvBOOST more expensive
    before = sushi.getAmountsOut(12*1e18, pathBOOST)[1]
    sushi.swapExactETHForTokens(0,pathBOOST,a,math.ceil(time.time()+1e6),{'from':a,'value':100e18})
    sushi.swapExactETHForTokens(0,pathBOOST,a2,math.ceil(time.time()+1e6),{'from':a2,'value':100e18})
    sushi.swapExactETHForTokens(0,pathBOOST,a3,math.ceil(time.time()+1e6),{'from':a3,'value':100e18})
    sushi.swapExactETHForTokens(0,pathBOOST,eth_whale,math.ceil(time.time()+1e6),{'from':eth_whale,'value':1000e18})
    after = sushi.getAmountsOut(12*1e18, pathBOOST)[1]
    print("12 ETH gets this many yvboost before",before/1e18)
    print("12 ETH gets this many yvboost after",after/1e18)
    assert after < before
    tx2 = strategy.harvest()
    after = sushi.getAmountsOut(12*1e18, pathCRV)
    print(tx2.events['BuyOrMint']['shouldMint'])
    assert tx2.events['BuyOrMint']['shouldMint'] == True
    
    # withdrawal    
    vault.withdraw({"from": user})
    assert token.balanceOf(user) != 0
    strategy.setBuffer(40, {"from": gov}) # increase buffer to 4%
    strategy.restoreApprovals({"from":gov}) # make sure reset approvals works
    strategy.setProxy("0xA420A63BbEFfbda3B147d0585F1852C358e2C152",{"from":gov})