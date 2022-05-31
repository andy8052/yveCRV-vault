// SPDX-License-Identifier: AGPL-3.0
// Feel free to change the license, but this is what we use

// Feel free to change this version of Solidity. We support >=0.6.0 <0.7.0;
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

// These are the core Yearn libraries
import {
    BaseStrategy
} from "@yearnvaults/contracts/BaseStrategy.sol";
import {
    SafeERC20,
    SafeMath,
    IERC20,
    Address
} from "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";


interface ITradeFactory {
    function enable(address, address) external;
}
interface ISwap {
    function getAmountsOut(
        uint amountIn,
        address[] memory path
    )
    external view returns (
        uint[] memory amounts
    );
}

interface IVoterProxy {
    function lock() external;
}

interface IyveCRV {
    function claimable(address) external view returns(uint256);
    function supplyIndex(address) external view returns(uint256);
    function balanceOf(address) external view returns(uint256);
    function index() external view returns(uint256);
    function claim() external;
    function depositAll() external;
}

contract Strategy is BaseStrategy {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    address internal tradeFactory;
    address internal proxy = 0xA420A63BbEFfbda3B147d0585F1852C358e2C152;
    IERC20 internal constant crv3 = IERC20(0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490);

    constructor(address _vault) BaseStrategy(_vault) public {
    }

    function name() external view override returns (string memory) {
        return "StrategyYearnVECRV";
    }

    function estimatedTotalAssets() public view override returns (uint256) {
        return want.balanceOf(address(this));
    }

    function prepareReturn(uint256 _debtOutstanding)
        internal
        override
        returns (
            uint256 _profit,
            uint256 _loss,
            uint256 _debtPayment
        ) {
        require(tradeFactory != address(0), "!tf");

        if (_debtOutstanding > 0) {
            (_debtPayment, _loss) = liquidatePosition(_debtOutstanding);
        }

        uint256 _claimable = getClaimable3Crv();
        if (_claimable > 0) {
            IyveCRV(address(want)).claim();
        }

        uint256 debt = vault.strategies(address(this)).totalDebt;
        uint256 assets = estimatedTotalAssets();
        if (assets >= debt){
            _profit = assets.sub(debt);
        } else {
            _loss = debt.sub(assets);
        }
    }

    // Here we lock curve in the voter contract. Lock doesn't require approval.
    function adjustPosition(uint256 _debtOutstanding) internal override {
        IVoterProxy(proxy).lock();
    }

    function liquidatePosition(uint256 _amountNeeded)
        internal
        override
        returns (uint256 _liquidatedAmount, uint256 _loss)
    {
        uint256 totalAssets = want.balanceOf(address(this));
        if (_amountNeeded > totalAssets) {
            _liquidatedAmount = totalAssets;
            _loss = _amountNeeded.sub(totalAssets);
        } else {
            _liquidatedAmount = _amountNeeded;
        }
    }

    function liquidateAllPositions()
        internal
        override
        returns (uint256 _amountFreed)
    {
        (_amountFreed, ) = liquidatePosition(estimatedTotalAssets());
    }

    function prepareMigration(address _newStrategy) internal override {
        uint256 balance3crv = balanceOf3crv();
        if(balance3crv > 0){
            crv3.safeTransfer(_newStrategy, balance3crv);
        }

        uint256 balanceYveCrv = want.balanceOf(address(this));
        if(balanceYveCrv > 0) {
            IERC20(want).safeTransfer(_newStrategy, balanceYveCrv);
        }
    }

    function ethToWant(uint256 _amtInWei)
        public
        view
        virtual
        override
        returns (uint256)
    {
        ISwap sushiRouter = ISwap(0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F);
        address[] memory path = new address[](2);
        path[0] = address(0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2); // WETH
        path[1] = address(0x9d409a0A012CFbA9B15F6D4B36Ac57A46966Ab9a); // yvBOOST
        return sushiRouter.getAmountsOut(_amtInWei, path)[1];
    }

    function balanceOf3crv() public view returns (uint256) {
        return crv3.balanceOf(address(this));
    }

    function getClaimable3Crv() public view returns (uint256) {
        IyveCRV YveCrv = IyveCRV(address(want));
        uint256 claimable = YveCrv.claimable(address(this));
        uint256 claimableToAdd = (YveCrv.index().sub(YveCrv.supplyIndex(address(this))))
            .mul(YveCrv.balanceOf(address(this)))
            .div(1e18);
        return claimable.mul(1e18).add(claimableToAdd);
    }

    // Common API used to update Yearn's StrategyProxy if needed in case of upgrades.
    function setProxy(address _proxy) external onlyGovernance {
        proxy = _proxy;
    }

    // internal helpers
    function protectedTokens()
        internal
        view
        override
        returns (address[] memory)
    {}

    // ----------------- YSWAPS FUNCTIONS ---------------------

    function setTradeFactory(address _tradeFactory) external onlyGovernance {
        if (tradeFactory != address(0)) {
            _removeTradeFactoryPermissions();
        }

        // approve and set up trade factory
        crv3.safeApprove(_tradeFactory, type(uint256).max);
        ITradeFactory tf = ITradeFactory(_tradeFactory);
        tf.enable(address(crv3), address(want));
        tradeFactory = _tradeFactory;
    }

    function removeTradeFactoryPermissions() external onlyEmergencyAuthorized {
        _removeTradeFactoryPermissions();

    }
    function _removeTradeFactoryPermissions() internal {
        crv3.safeApprove(tradeFactory, 0);
        tradeFactory = address(0);
    }
}
