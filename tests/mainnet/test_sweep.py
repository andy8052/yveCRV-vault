import brownie

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