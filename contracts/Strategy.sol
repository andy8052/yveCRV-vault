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

import "./ySwap/SwapperEnabled.sol";

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

contract Strategy is BaseStrategy, SwapperEnabled {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    address internal constant crv3 = 0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490;
    address internal proxy = 0xA420A63BbEFfbda3B147d0585F1852C358e2C152;

    constructor(address _vault, address _tradeFactory) BaseStrategy(_vault) SwapperEnabled(_tradeFactory) public {
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

        if (_debtOutstanding > 0) {
            (_debtPayment, _loss) = liquidatePosition(_debtOutstanding);
        }

        uint256 _claimable = getClaimable3Crv();
        if (_claimable > 0) {
            IyveCRV(address(want)).claim();
        }

        uint256 _balance3crv = balanceOf3crv();
        if (_balance3crv > 0) {
            uint256 _allowance = _tradeFactoryAllowance(crv3);
            _createTrade(
                crv3,
                address(want),
                _balance3crv - _allowance,
                block.timestamp + 604800
            );
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

    function prepareMigration(address _newStrategy) internal override {
        uint256 balance3crv = balanceOf3crv();
        if(balance3crv > 0){
            IERC20(crv3).safeTransfer(_newStrategy, balance3crv);
        }

        uint256 balanceYveCrv = IERC20(address(want)).balanceOf(address(this));
        if(balanceYveCrv > 0) {
            IERC20(address(want)).safeTransfer(_newStrategy, balanceYveCrv);
        }
    }

    function balanceOf3crv() public view returns (uint256) {
        return IERC20(crv3).balanceOf(address(this));
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

    function deposityveCRV() internal {
        IyveCRV(address(want)).depositAll();
    }

    // internal helpers
    function protectedTokens()
        internal
        view
        override
        returns (address[] memory)
    {}
}
