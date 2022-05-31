from brownie import Contract


def test_operation(accounts, token, vault, yveCrv, strategy, strategist, amount, user, crv3, chain, whale_3crv, gov, klim):
    chain.snapshot()
    vault_before = token.balanceOf(vault)
    strat_before = token.balanceOf(strategy)
    # Deposit to the vault
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount + vault_before

    # Move funds to strat
    strategy.harvest({"from":strategist})
    assert token.balanceOf(strategy.address) == amount + vault_before + strat_before

    # Done to fix the UniswapV2: K issue
    pairs = [strategy.ethCrvPair(), strategy.ethYvBoostPair(), strategy.ethUsdcPair()]
    for pair in pairs:
        Contract.from_explorer(pair, owner=strategist).sync()

    # harvest to accrue strategist reward as this is part of our test
    # to make sure that these yvBOOST shares are separated from the purhcased
    # amount and not used to withdraw yveCRV from vault
    strategist_reward_before = vault.balanceOf(strategy)
    crv3.transfer(strategy, 10e20, {"from": whale_3crv})
    strategy.harvest({"from":strategist})
    chain.sleep(60*60*6) # sleep to increase pps
    chain.mine(1)

    strategist_reward_before = vault.balanceOf(strategy)
    yveCrv.transfer(strategy, 10e20, {"from": klim})
    tx = strategy.harvest({"from":strategist})
    print(tx.events["Harvested"])
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
    assert False