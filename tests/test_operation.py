import brownie, math, time
from helpers import showBalances
from brownie import Contract
import time


def test_operation(accounts, token, vault, strategy, strategist, amount, user, crv3, chain, whale_3crv, gov):
    chain.snapshot()
    # Deposit to the vault
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount

    # Move funds to strat
    strategy.harvest()
    assert token.balanceOf(strategy.address) == amount

    # Done to fix the UniswapV2: K issue
    pairs = [strategy.ethCrvPair(), strategy.ethYvBoostPair(), strategy.ethUsdcPair()]
    for pair in pairs:
        Contract.from_explorer(pair, owner=strategist).sync()

    # harvest using BUY route
    chain.snapshot()
    a = accounts[7]
    sushi = Contract("0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F")
    path = [
        "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",   # WETH
        "0xD533a949740bb3306d119CC777fa900bA034cd52"   # CRV
    ]
    sushi.swapExactETHForTokens(0,path,a,math.ceil(time.time()),{'from':a,'value':100e18})
    crv3.transfer(strategy, 10e20, {"from": whale_3crv})
    tx1 = strategy.harvest()
    print(tx2.events['BuyOrMint'])
    chain.revert()
    crv3.transfer(strategy, 10e20, {"from": whale_3crv})
    tx2 = strategy.harvest()
    print(tx2.events['BuyOrMint'])
    assert False

    # withdrawal
    vault.withdraw({"from": user})
    assert token.balanceOf(user) != 0
    strategy.setBuffer(40, {"from": gov}) # increase buffer to 4%
    strategy.restoreApprovals({"from":gov}) # make sure reset approvals works
    chain.revert()

def test_emergency_exit(accounts, token, vault, strategy, strategist, amount, user):
    # Deposit to the vault
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    strategy.harvest()
    assert token.balanceOf(strategy.address) == amount

    # set emergency and exit
    strategy.setEmergencyExit()
    strategy.harvest()
    assert token.balanceOf(strategy.address) < amount

def test_set_buffer(gov, token, vault, strategy, strategist):
    # Deposit to the vault and harvest
    strategy.setBuffer(20, {"from": gov})

def test_change_debt(gov, token, vault, strategy, strategist, amount, user):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    vault.updateStrategyDebtRatio(strategy.address, 5_000, {"from": gov})
    strategy.harvest()

    assert token.balanceOf(strategy.address) == amount / 2

    vault.updateStrategyDebtRatio(strategy.address, 10_000, {"from": gov})
    strategy.harvest()
    assert token.balanceOf(strategy.address) == amount

    # In order to pass this tests, you will need to implement prepareReturn.
    # TODO: uncomment the following lines.
    # vault.updateStrategyDebtRatio(strategy.address, 5_000, {"from": gov})
    # assert token.balanceOf(strategy.address) == amount / 2


def test_sweep(gov, vault, strategy, token, amount, weth, weth_amount):
    # Strategy want token doesn't work
    token.transfer(strategy, amount, {"from": gov})
    assert token.address == strategy.want()
    assert token.balanceOf(strategy) > 0
    with brownie.reverts("!want"):
        strategy.sweep(token, {"from": gov})

    # Vault share token doesn't work
    with brownie.reverts("!shares"):
        strategy.sweep(vault.address, {"from": gov})

    before_balance = weth.balanceOf(gov)
    weth.transfer(strategy, weth_amount, {"from": gov})
    assert weth.address != strategy.want()
    assert weth.balanceOf(gov) == before_balance - weth_amount
    strategy.sweep(weth, {"from": gov})
    assert weth.balanceOf(gov) == before_balance


def test_triggers(gov, vault, strategy, token, amount, weth, weth_amount, user):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    vault.updateStrategyDebtRatio(strategy.address, 5_000, {"from": gov})
    strategy.harvest()
    strategy.harvestTrigger(0)
    strategy.tendTrigger(0)