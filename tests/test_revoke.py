def test_revoke_strategy_from_vault(token, vault, strategy, amount, gov, user):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    strategy.harvest()
    assert strategy.estimatedTotalAssets() == amount

    vault.revokeStrategy(strategy.address, {"from": gov})
    strategy.harvest()
    assert token.balanceOf(vault.address) == amount


def test_revoke_strategy_from_strategy(token, vault, strategy, amount, gov, user):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    strategy.harvest()
    assert strategy.estimatedTotalAssets() == amount

    strategy.setEmergencyExit()
    strategy.harvest()
    assert token.balanceOf(vault.address) == amount
