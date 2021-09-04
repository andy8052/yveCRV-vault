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

interface ISwap {
    function swapExactTokensForTokens(
        uint256,
        uint256,
        address[] calldata,
        address,
        uint256
    ) external;
    function getAmountsOut(uint amountIn, address[] memory path) external view returns (uint[] memory amounts);
}

interface Pair {
    function getReserves() external view returns (
        uint112,
        uint112,
        uint32
    );
}

interface ICurveFi {
    function calc_withdraw_one_coin(uint256, int128) external view returns(uint256);
    function remove_liquidity_one_coin(uint256, int128, uint256) external;
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

library UniswapV2Library {
    using SafeMath for uint;
    function getAmountOut(uint amountIn, uint reserveIn, uint reserveOut) internal pure returns (uint amountOut) {
        require(amountIn > 0, 'UniswapV2Library: INSUFFICIENT_INPUT_AMOUNT');
        require(reserveIn > 0 && reserveOut > 0, 'UniswapV2Library: INSUFFICIENT_LIQUIDITY');
        uint amountInWithFee = amountIn.mul(997);
        uint numerator = amountInWithFee.mul(reserveOut);
        uint denominator = reserveIn.mul(1000).add(amountInWithFee);
        amountOut = numerator / denominator;
    }
}

contract Strategy is BaseStrategy {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    address public constant yvBoost        = address(0x9d409a0A012CFbA9B15F6D4B36Ac57A46966Ab9a);
    address public constant crv            = address(0xD533a949740bb3306d119CC777fa900bA034cd52);
    address public constant usdc           = address(0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48);
    address public constant crv3           = address(0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490);
    address public constant crv3Pool       = address(0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7);
    address public constant weth           = address(0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2);
    address public constant sushiswap      = address(0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F);
    address public constant ethCrvPair     = address(0x58Dc5a51fE44589BEb22E8CE67720B5BC5378009); // Sushi
    address public constant ethYvBoostPair = address(0x9461173740D27311b176476FA27e94C681b1Ea6b); // Sushi
    address public constant ethUsdcPair    = address(0x397FF1542f962076d0BFE58eA045FfA2d347ACa0);
    address public proxy                   = address(0xA420A63BbEFfbda3B147d0585F1852C358e2C152);
    
    // Configurable preference for locking CRV in vault vs market-buying yvBOOST. 
    // Default: Buy only when yvBOOST price becomes > 3% price of CRV
    uint256 public vaultBuffer          = 30;
    uint256 public constant DENOMINATOR = 1000;

    event UpdatedBuffer(uint256 newBuffer);
    event BuyOrMint(bool shouldMint, uint256 projBuyAmount, uint256 projMintAmount);

    constructor(address _vault) public BaseStrategy(_vault) {
        // You can set these parameters on deployment to whatever you want
        IERC20(crv).safeApprove(address(want), type(uint256).max);
        IERC20(usdc).safeApprove(sushiswap, type(uint256).max);
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
        )
    {
        if (_debtOutstanding > 0) {
            (_debtPayment, _loss) = liquidatePosition(_debtOutstanding);
        }

        // Figure out how much want we have
        uint256 claimable = getClaimable3Crv();
        claimable = claimable > 0 ? claimable : IERC20(crv3).balanceOf(address(this)); // We do this to make testing harvest easier
        uint256 debt = vault.strategies(address(this)).totalDebt;
        if (claimable > 0 || estimatedTotalAssets() > debt) {
            IyveCRV(address(want)).claim();
            withdrawFrom3CrvToUSDC(); // Convert 3crv to USDC
            uint256 usdcBalance = IERC20(usdc).balanceOf(address(this));
            if(usdcBalance > 0){
                // Aquire yveCRV either via:
                //  1) buy CRV and mint or 
                //  2) market-buy yvBOOST and unwrap
                if(shouldMint(usdcBalance)){
                    swap(usdc, crv, usdcBalance);
                    deposityveCRV(); // Mints yveCRV
                }
                else{
                    // Avoid rugging pre-existing strategist rewards (which are denominated in same token we're swapping fore)
                    uint256 strategistRewards = vault.balanceOf(address(this));
                    swap(usdc, yvBoost, usdcBalance);
                    uint256 swapGain = vault.balanceOf(address(this)).sub(strategistRewards);
                    if(swapGain > 0){
                        // Here we burn our new vault shares. But because strategy is withdrawing to itself,
                        // the want balance will not increase. Overall strategy debt is reduced, while want balance stays the same.
                        vault.withdraw(swapGain);
                        // The withdraw action above reduces the strategy's debt, so let's update this value we set earlier.
                        debt = vault.strategies(address(this)).totalDebt;
                    }
                }
            }
            uint256 assets = estimatedTotalAssets();
            if(assets >= debt){
                _profit = assets.sub(debt);
            }
            else{
                _loss = debt.sub(assets);
            }
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

    // NOTE: Can override `tendTrigger` and `harvestTrigger` if necessary

    function prepareMigration(address _newStrategy) internal override {
        uint256 balance3crv = IERC20(crv3).balanceOf(address(this));
        uint256 balanceYveCrv = IERC20(address(want)).balanceOf(address(this));
        if(balance3crv > 0){
            IERC20(crv3).safeTransfer(_newStrategy, balance3crv);
        }
        if(balanceYveCrv > 0){
            IERC20(address(want)).safeTransfer(_newStrategy, balanceYveCrv);
        }
        IERC20(crv).safeApprove(address(want), 0);
        IERC20(usdc).safeApprove(sushiswap, 0);
    }

    // Here we determine if better to market-buy yvBOOST or mint it via backscratcher
    function shouldMint(uint256 _amountIn) internal returns (bool) {
        // Using reserve ratios of swap pairs will allow us to compare whether it's more efficient to:
        //  1) Buy yvBOOST (unwrapped for yveCRV)
        //  2) Buy CRV (and use to mint yveCRV 1:1)
        address[] memory path = new address[](3);
        path[0] = usdc;
        path[1] = weth;
        path[2] = yvBoost;
        uint256[] memory amounts = ISwap(sushiswap).getAmountsOut(_amountIn, path);
        uint256 projectedYvBoost = amounts[2];
        // Convert yvBOOST to yveCRV
        uint256 projectedYveCrv = projectedYvBoost.mul(vault.pricePerShare()).div(1e18); // save some gas by hardcoding 1e18

        path = new address[](3);
        path[0] = usdc;
        path[1] = weth;
        path[2] = crv;
        amounts = ISwap(sushiswap).getAmountsOut(_amountIn, path);
        uint256 projectedCrv = amounts[2];

        // Here we favor minting by a % value defined by "vaultBuffer"
        bool shouldMint = projectedCrv.mul(DENOMINATOR.add(vaultBuffer)).div(DENOMINATOR) > projectedYveCrv;
        emit BuyOrMint(shouldMint, projectedYveCrv, projectedCrv);

        return shouldMint;
    }

    function withdrawFrom3CrvToUSDC() internal {
        uint256 amount = IERC20(crv3).balanceOf(address(this));
        if(amount > 0){
            ICurveFi(crv3Pool).remove_liquidity_one_coin(amount, 1, 0);
        }
    }

    function quoteWithdrawFrom3Crv(uint256 _amount) internal view returns(uint256) {
        return ICurveFi(crv3Pool).calc_withdraw_one_coin(_amount, 1);
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

    function swap(address token_in, address token_out, uint256 amount_in) internal {
        // Don't swap if amount in is 0
        if(amount_in == 0){
            return;
        }
        bool is_weth = token_in == weth || token_out == weth;
        address[] memory path = new address[](is_weth ? 2 : 3);
        path[0] = token_in;
        if (is_weth) {
            path[1] = token_out;
        } else {
            path[1] = weth;
            path[2] = token_out;
        }
        ISwap(sushiswap).swapExactTokensForTokens(
            amount_in,
            0,
            path,
            address(this),
            now
        );
    }

    function deposityveCRV() internal {
        IyveCRV(address(want)).depositAll();
    }

    function setBuffer(uint256 _newBuffer) external onlyGovernance {
        require(_newBuffer < DENOMINATOR, "!TooHigh");
        vaultBuffer = _newBuffer;
        emit UpdatedBuffer(_newBuffer);
    }

    function restoreApprovals() external onlyGovernance {
        IERC20(crv).safeApprove(address(want), 0); // CRV must go to zero first before increase
        IERC20(usdc).safeApprove(sushiswap, 0); // USDC must go to zero first before increase
        IERC20(crv).safeApprove(address(want), type(uint256).max);
        IERC20(usdc).safeApprove(sushiswap, type(uint256).max);
    }

    // internal helpers
    function protectedTokens()
        internal
        view
        override
        returns (address[] memory)
    {
        address[] memory protected = new address[](2);
        protected[0] = crv3;
        protected[1] = usdc;
        return protected;
    }
}
