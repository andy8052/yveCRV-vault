from brownie import Strategy, accounts, config, network, project, web3
from brownie import Contract



def main():
    strategist = accounts.load('deployer')
    sms = '0x16388463d60FFE0661Cf7F1f31a7D658aC790ff7'
    vault = Contract('0x9d409a0A012CFbA9B15F6D4B36Ac57A46966Ab9a')
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
    strategy = strategist.deploy(Strategy, vault)

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
    # ms = accounts.at("0x16388463d60ffe0661cf7f1f31a7d658ac790ff7", force=True)
    # sharer = Contract("0x2C641e14AfEcb16b4Aa6601A40EE60c3cc792f7D", owner=ms)
    #sharerv3 = Contract("0x2C641e14AfEcb16b4Aa6601A40EE60c3cc792f7D", owner=ms)

    sharerv4 = Contract("0xc491599b9A20c3A2F0A85697Ee6D9434EFa9f503")
    wavey = "0x6AFB7c9a6E8F34a3E0eC6b734942a5589A84F44C"
    andy = "0xfbAcB28f49954064c57f7Bd7F001B758Bc7415ba"
    patrick = "0xb3067e47d005f9A588162A710071d18098c93E04"
    dude = "0x8Ef63b525fceF7f8662D98F77f5C9A86ae7dFE09"
    poolpi = "0x05B7D0dfdD845c58AbC8B78b02859b447b79ed34"
    facu = "0x334CE923420ff1aA4f272e92BF68013D092aE7B4"
    sharerv4.setContributors(
        strategy,
        [wavey, andy, patrick, dude, facu, poolpi],
        [450, 250, 85, 85, 80, 50],
        {"from":strategist}
    )
    strategy.setRewards(sharerv4.address)
    old_strat = "0xBfdD0b4f6Ab0D24896CAf8C892838C26C8b0F7be"
    sharerv4.distribute(old_strat)
    strategy.setKeeper("0x736D7e3c5a6CB2CE3B764300140ABF476F6CFCCF")

    s = Strategy.at("0x2923a58c1831205C854DBEa001809B194FDb3Fa5")
    Strategy.publish_source(s)

    # strategy = Contract(strategy, owner=strategist)
    
    # strategy.setRewards(sharerv4.address)
    # strategy.setKeeper("0x736D7e3c5a6CB2CE3B764300140ABF476F6CFCCF")

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

    gov = accounts.at("0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52", force=True)

    def update_yvBOOST_strategy():
        safe        = ApeSafe("ychad.eth")
        vault       = safe.contract("0x9d409a0A012CFbA9B15F6D4B36Ac57A46966Ab9a")
        
        live_strat  = "0xBfdD0b4f6Ab0D24896CAf8C892838C26C8b0F7be"
        new_strat   = "0x2923a58c1831205C854DBEa001809B194FDb3Fa5"
        vault.migrateStrategy(live_strat, new_strat)

        safe_tx     = safe.multisend_from_recipients()
        safe.preview(safe_tx, call_trace=False)
        safe.post_transaction(safe_tx)