def test_triggers(gov, vault, strategy, token, amount, weth, weth_amount, user, strategist):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    vault.updateStrategyDebtRatio(strategy.address, 5_000, {"from": gov})
    strategy.harvest({"from":strategist})
    strategy.harvestTrigger(0)
    strategy.tendTrigger(0)