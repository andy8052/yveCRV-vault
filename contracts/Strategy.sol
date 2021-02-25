// SPDX-License-Identifier: AGPL-3.0
// Feel free to change the license, but this is what we use

// Feel free to change this version of Solidity. We support >=0.6.0 <0.7.0;
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

// These are the core Yearn libraries
import {
    BaseStrategy,
    StrategyParams
} from "@yearnvaults/contracts/BaseStrategy.sol";
import {
    SafeERC20,
    SafeMath,
    IERC20,
    Address
} from "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";

interface Swap {
    function swapExactTokensForTokens(
        uint256,
        uint256,
        address[] calldata,
        address,
        uint256
    ) external;
    
    function getAmountsOut(uint amountIn, address[] memory path) external view returns (uint[] memory amounts);
}

interface ICurveFi {
    function calc_withdraw_one_coin(uint256, int128) external view returns(uint256);
    function remove_liquidity_one_coin(uint256, int128, uint256) external;
}

interface IyveCRV {
    function claimable(address) external view returns(uint256);
    function claim() external;
    function depositAll() external;
}

contract Strategy is BaseStrategy {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    address public constant crv       = 0xD533a949740bb3306d119CC777fa900bA034cd52;
    address public constant usdc      = 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48;
    address public constant crv3      = 0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7;
    address public constant weth      = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    address public constant reward    = 0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490;
    address public constant sushiswap = 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F;

    constructor(address _vault) public BaseStrategy(_vault) {
        // You can set these parameters on deployment to whatever you want
        // maxReportDelay = 6300;
        // profitFactor = 100;
        // debtThreshold = 0;
        IERC20(crv).safeApprove(address(want), type(uint256).max);
        IERC20(usdc).safeApprove(sushiswap, type(uint256).max);
    }

    // ******** OVERRIDE THESE METHODS FROM BASE CONTRACT ************

    function name() external view override returns (string memory) {
        return "StrategyYearnVECRV";
    }

    function estimatedTotalAssets() public view override returns (uint256) {
        uint256 claimable = IyveCRV(address(want)).claimable(address(this));
        uint256 stable = quoteWithdrawFromCrv(claimable);
        uint256 estveCrv = quote(usdc, address(want), stable);
        return want.balanceOf(address(this)).add(estveCrv);
    }

    function prepareReturn(uint256 _debtOutstanding)
        internal
        override
        returns (
            uint256 _profit,
            uint256 _loss,
            uint256 _debtPayment
        )
    {
        if (_debtOutstanding > 0) {
            (_debtPayment, _loss) = liquidatePosition(_debtOutstanding);
        }

        // Figure out how much want we have
        uint256 before = want.balanceOf(address(this));

        uint256 claimable = IyveCRV(address(want)).claimable(address(this));
        if (claimable > 0) {
            IyveCRV(address(want)).claim();
            withdrawFromCrv();
            swap(usdc, crv, IERC20(usdc).balanceOf(address(this)));
            deposityveCRV();
        }
    }

    // we do not need to do anything here. Holding veCRV is enough
    function adjustPosition(uint256 _debtOutstanding) internal override {
        return;
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

    // NOTE: Can override `tendTrigger` and `harvestTrigger` if necessary

    function prepareMigration(address _newStrategy) internal override {
        // TODO: Transfer any non-`want` tokens to the new strategy
        // NOTE: `migrate` will automatically forward all `want` in this strategy to the new one
        return;
    }

    // internal helpers

    function protectedTokens()
        internal
        view
        override
        returns (address[] memory)
    {
        address[] memory protected = new address[](2);
        protected[0] = address(want);
        protected[1] = reward;
        protected[2] = usdc;
        return protected;
    }

    function withdrawFromCrv() internal {
        uint256 remove = IERC20(reward).balanceOf(address(this));
        ICurveFi(crv3).remove_liquidity_one_coin(remove, 1, 0);
    }

    function quoteWithdrawFromCrv(uint256 _amount) internal view returns(uint256) {
        return ICurveFi(crv3).calc_withdraw_one_coin(_amount, 1);
    }

    function quote(address token_in, address token_out, uint256 amount_in) internal view returns (uint256) {
        bool is_weth = token_in == weth || token_out == weth;
        address[] memory path = new address[](is_weth ? 2 : 3);
        path[0] = token_in;
        if (is_weth) {
            path[1] = token_out;
        } else {
            path[1] = weth;
            path[2] = token_out;
        }
        uint256[] memory amounts = Swap(sushiswap).getAmountsOut(amount_in, path);
        return amounts[amounts.length - 1];
    }
    
    function swap(address token_in, address token_out, uint amount_in) internal {
        bool is_weth = token_in == weth || token_out == weth;
        address[] memory path = new address[](is_weth ? 2 : 3);
        path[0] = token_in;
        if (is_weth) {
            path[1] = token_out;
        } else {
            path[1] = weth;
            path[2] = token_out;
        }
        Swap(sushiswap).swapExactTokensForTokens(
            amount_in,
            0,
            path,
            address(this),
            block.timestamp
        );
    }

    function deposityveCRV() internal {
        IyveCRV(address(want)).depositAll();
    }
}
