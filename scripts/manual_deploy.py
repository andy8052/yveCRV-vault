from brownie import Strategy, accounts, config, network, project, web3
from brownie import Contract



def main():
    strategist = accounts.load('deployer')
    sms = '0x16388463d60FFE0661Cf7F1f31a7D658aC790ff7'
    # token = '0xc5bDdf9843308380375a611c18B50Fb9341f502A'
    # governance = '0x6AFB7c9a6E8F34a3E0eC6b734942a5589A84F44C' # ryan deployer account
    # guardian = '0x846e211e8ba920B353FB717631C015cf04061Cc9' # dev.ychad.eth
    # treasury = '0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52' # treasury.ychad.eth
    # name = 'Yearn Compounding veCRV yVault'
    # symbol = 'yvBOOST'
    
    # registry = Contract('0x50c1a2eA0a861A967D9d0FFE2AE4012c2E053804') # v2.registry.ychad.eth
    # tx = registry.newExperimentalVault(token, governance, guardian, treasury, name, symbol, {"from": strategist})
    # print(tx.events)

    # STRATEGY DEPLOY + SETUP
    vault = Contract('0x9d409a0A012CFbA9B15F6D4B36Ac57A46966Ab9a')
    
    
    #strategy = strategist.deploy(Strategy, vault)

    strategy = Contract('0x43DC3A717F7436ebC924e547B586C7e2896Cef9C')
    # debt_ratio = 10_000                 # 98%
    # minDebtPerHarvest = 0             # Lower limit on debt add
    # maxDebtPerHarvest = 2 ** 256 - 1  # Upper limit on debt add
    # performance_fee = 1000            # Strategist perf fee: 10%

    # vault.addStrategy(
    #     strategy, 
    #     debt_ratio, 
    #     minDebtPerHarvest,
    #     maxDebtPerHarvest,
    #     performance_fee, 
    #     {'from': strategist}
    # )
    
    # STRATEGY CONFIG 

    ## SHARER V3
    # sharer = Contract('0x2C641e14AfEcb16b4Aa6601A40EE60c3cc792f7D')
    # ryan = strategist.address
    # andy = '0xfbAcB28f49954064c57f7Bd7F001B758Bc7415ba'
    # sharer.setContributors(
    #     strategy,
    #     [ryan,andy],
    #     [650,250], ## Ryan = 650, Andy = 250, SMS = remainder
    #     {'from': strategist}
    # )
    # strategy.setRewards(sharer.address, {'from': strategist})

    # keep3r_manager = '0x13dAda6157Fee283723c0254F43FF1FdADe4EEd6'
    
    
    # strategy.setKeeper(keep3r_manager, {'from': strategist})
    # vault.setManagement(sms, {'from': strategist})
    # vault.setGovernance('0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52', {'from': strategist})

    # vault = Contract('0x9d409a0A012CFbA9B15F6D4B36Ac57A46966Ab9a') 
    # strategy = Contract('0x43DC3A717F7436ebC924e547B586C7e2896Cef9C') 
    # registry = Contract('0x50c1a2eA0a861A967D9d0FFE2AE4012c2E053804')

    # # For GOV
    # vault.acceptGovernance()
    # vault.setManagementFee(0, {'from': ychad.eth})
    # vault.setPerformanceFee(0, {'from': ychad.eth})
    # registry.endorseVault(vault, {'from': ychad.eth})