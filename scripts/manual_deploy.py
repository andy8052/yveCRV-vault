from brownie import Strategy, accounts, config, network, project, web3
from brownie import Contract



def main():
    strategist = accounts.load('deployer')
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
    
    
    strategy = strategist.deploy(Strategy, vault)


    # debt_ratio = 9800                 # 98%
    # minDebtPerHarvest = 0             # Lower limit on debt add
    # maxDebtPerHarvest = 2 ** 256 - 1  # Upper limit on debt add
    # performance_fee = 1000            # Strategist perf fee: 10%

    # vault.addStrategy(
    #     strategy, 
    #     debt_ratio, 
    #     minDebtPerHarvest,
    #     maxDebtPerHarvest,
    #     performance_fee, 
    #     1_000, {'from': strategist}
    # )
    
    # STRATEGY SETUP
    # sharer = Contract('0x2C641e14AfEcb16b4Aa6601A40EE60c3cc792f7D')

    # keep3r_manager = '0x13dAda6157Fee283723c0254F43FF1FdADe4EEd6'
    # strategy.setKeeper(keep3r_manager)

    # # SHARER V3
    # # Ryan = 650, Andy = 250, SMS = Remainder
    # ryan = strategist.address
    # andy = ''
    # sharer.setContributors(
    #     address strategy,
    #     [ryan,andy],
    #     [650,250]
    # )