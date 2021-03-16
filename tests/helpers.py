from itertools import count
from brownie import Wei, reverts, network
import brownie
import requests


def showBalances(token, vault, strategy, yveCrv, weth, usdc, crv3):
    print("\n----Vault Balances----")
    print("yveCRV:", yveCrv.balanceOf(vault) / 1e18)
    print("\n-----Strategy Balances----")
    print("yveCRV:", yveCrv.balanceOf(strategy) / 1e18)
    print("3Crv:", crv3.balanceOf(strategy) / 1e18)
    print("USDC:", usdc.balanceOf(strategy) / 1e18)
