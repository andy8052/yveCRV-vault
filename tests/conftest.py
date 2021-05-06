import pytest
from brownie import config
from brownie import Contract


@pytest.fixture
def gov(accounts):
    yield accounts.at("0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52", force=True)

@pytest.fixture
def user(accounts):
    yield accounts[0]

@pytest.fixture
def rewards(accounts):
    yield accounts[1]


@pytest.fixture
def guardian(accounts):
    yield accounts[2]


@pytest.fixture
def management(accounts):
    yield accounts[3]


@pytest.fixture
def strategist(accounts):
    yield accounts[4]


@pytest.fixture
def keeper(accounts):
    yield accounts[5]


@pytest.fixture
def rando(accounts):
    yield accounts[6]


@pytest.fixture
def token():
    token_address = "0xc5bDdf9843308380375a611c18B50Fb9341f502A"  # this should be the address of the ERC-20 used by the strategy/vault
    yield Contract(token_address)


@pytest.fixture
def crv():
    yield Contract("0xD533a949740bb3306d119CC777fa900bA034cd52")


@pytest.fixture
def amount(accounts, token, gov):
    amount = 10_000 * 10 ** token.decimals()
    # In order to get some funds for the token you are about to use,
    # it impersonate an exchange address to use it's funds.
    reserve = accounts.at("0x10B47177E92Ef9D5C6059055d92DdF6290848991", force=True)
    token.transfer(accounts[0], amount, {"from": reserve})
    token.transfer(gov, amount, {"from": reserve})
    yield amount


@pytest.fixture
def vault(pm, gov, rewards, guardian, management, token):
    yield Contract("0x9d409a0A012CFbA9B15F6D4B36Ac57A46966Ab9a")

@pytest.fixture
def strategy(strategist, keeper, vault, Strategy, gov):
    old_strat = Contract(vault.withdrawalQueue(0))
    strategy = strategist.deploy(Strategy, vault)
    strategy.setKeeper(keeper)
    vault.migrateStrategy(old_strat, strategy, {'from':gov})
    # Fix k error
    pairs = [strategy.ethCrvPair(), strategy.ethYvBoostPair(), strategy.ethUsdcPair()]
    for pair in pairs:
        Contract.from_explorer(pair, owner=strategist).sync()
    yield strategy





@pytest.fixture
def crv3():
    yield Contract("0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490")


@pytest.fixture
def usdc():
    yield Contract("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")


@pytest.fixture
def weth():
    yield Contract("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")


@pytest.fixture
def yveCrvContract():
    yield Contract("0xc5bDdf9843308380375a611c18B50Fb9341f502A")


@pytest.fixture
def proxy(strategy, gov):
    p = Contract("0x9a165622a744C20E3B2CB443AeD98110a33a231b")
    p.approveStrategy(strategy.address, strategy.address, {"from":gov}) # Self address as gauge
    yield p


@pytest.fixture
def yveCrv(token):
    yield token


@pytest.fixture
def whale_eth(accounts):
    yield accounts.at("0x73BCEb1Cd57C711feaC4224D062b0F6ff338501e", force=True)


@pytest.fixture
def whale_3crv(accounts):
    yield accounts.at("0x43b4FdFD4Ff969587185cDB6f0BD875c5Fc83f8c", force=True)


@pytest.fixture
def sushiswap_crv(accounts):
    yield accounts.at("0x5c00977a2002a3C9925dFDfb6815765F578a804f", force=True)


@pytest.fixture
def sushiswap(accounts):
    yield Contract("0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F")

@pytest.fixture
def not_banteg(accounts):
    yield accounts.at("0x0035Fc5208eF989c28d47e552E92b0C507D2B318", force=True) # Definitely not banteg


@pytest.fixture
def weth_amount(accounts, weth, gov):
    amount = 1e21
    # In order to get some funds for the token you are about to use,
    # it impersonate an exchange address to use it's funds.
    reserve = accounts.at("0x2F0b23f53734252Bda2277357e97e1517d6B042A", force=True)
    weth.transfer(gov, amount, {"from": reserve})
    yield amount
