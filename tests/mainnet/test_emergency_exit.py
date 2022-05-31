def test_emergency_exit(accounts, token, vault, strategy, strategist, amount, user, chain):
    # Deposit to the vault
    vault_before = token.balanceOf(vault)
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    strategy.harvest({"from":strategist})
    assert token.balanceOf(strategy.address) == amount + vault_before

    # set emergency and exit
    strategy.setEmergencyExit()
    strategy.harvest({"from":strategist})
    # assert token.balanceOf(strategy.address) < amount + vault_before
    assert token.balanceOf(strategy.address) == 0