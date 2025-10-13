// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/**
 * @title CPT - Context Pilot Token
 * @author Context Pilot Team
 * @notice Developer incentive token for the Context Pilot ecosystem
 * 
 * Features:
 * - ERC-20 compliant
 * - Mintable by authorized agents (MINTER_ROLE)
 * - Burnable for inactive accounts (BURNER_ROLE)
 * - Monthly renewal cycles with supply control
 * - Pausable for emergency stops
 * 
 * Token Economics:
 * - No initial supply (generated via rewards)
 * - Max supply per cycle: 1,000,000 CPT
 * - Tokens expire after 30 days of inactivity
 * - Burned tokens reduce circulating supply
 */
contract CPT is ERC20, AccessControl, Pausable {
    
    // Roles
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant BURNER_ROLE = keccak256("BURNER_ROLE");
    
    // Supply controls
    uint256 public constant MAX_SUPPLY_PER_CYCLE = 1_000_000 * 10**18; // 1M tokens
    uint256 public currentCycleSupply;
    uint256 public cycleStartTime;
    uint256 public constant CYCLE_DURATION = 30 days;
    
    // Inactivity tracking
    mapping(address => uint256) public lastActivity;
    uint256 public constant INACTIVITY_PERIOD = 30 days;
    
    // Events
    event CycleRenewed(uint256 indexed cycleNumber, uint256 timestamp);
    event TokensBurned(address indexed account, uint256 amount, string reason);
    event TokensMinted(address indexed to, uint256 amount, string source);
    
    constructor() ERC20("Context Pilot Token", "CPT") {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, msg.sender);
        _grantRole(BURNER_ROLE, msg.sender);
        
        cycleStartTime = block.timestamp;
        emit CycleRenewed(1, cycleStartTime);
    }
    
    /**
     * @notice Mint tokens to a developer as reward
     * @param to Recipient address
     * @param amount Amount to mint (in base units)
     * @dev Only callable by MINTER_ROLE (rewards engine)
     */
    function mint(address to, uint256 amount) 
        external 
        onlyRole(MINTER_ROLE) 
        whenNotPaused 
    {
        require(to != address(0), "CPT: mint to zero address");
        require(amount > 0, "CPT: mint zero amount");
        
        // Check cycle supply limit
        require(
            currentCycleSupply + amount <= MAX_SUPPLY_PER_CYCLE,
            "CPT: cycle supply limit exceeded"
        );
        
        currentCycleSupply += amount;
        lastActivity[to] = block.timestamp;
        
        _mint(to, amount);
        emit TokensMinted(to, amount, "rewards");
    }
    
    /**
     * @notice Burn tokens from inactive account
     * @param account Account to burn from
     * @dev Only callable by BURNER_ROLE after inactivity period
     */
    function burnInactive(address account) 
        external 
        onlyRole(BURNER_ROLE) 
    {
        require(account != address(0), "CPT: burn from zero address");
        
        uint256 lastActive = lastActivity[account];
        require(
            block.timestamp >= lastActive + INACTIVITY_PERIOD,
            "CPT: account not inactive"
        );
        
        uint256 balance = balanceOf(account);
        require(balance > 0, "CPT: zero balance");
        
        _burn(account, balance);
        emit TokensBurned(account, balance, "inactivity");
    }
    
    /**
     * @notice Renew monthly cycle and reset supply counter
     * @dev Only callable by admin after cycle duration
     */
    function renewCycle() external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(
            block.timestamp >= cycleStartTime + CYCLE_DURATION,
            "CPT: cycle not ended"
        );
        
        uint256 cycleNumber = (block.timestamp - cycleStartTime) / CYCLE_DURATION + 1;
        cycleStartTime = block.timestamp;
        currentCycleSupply = 0;
        
        emit CycleRenewed(cycleNumber, cycleStartTime);
    }
    
    /**
     * @notice Get time until next cycle renewal
     * @return seconds until renewal is possible
     */
    function timeUntilRenewal() external view returns (uint256) {
        uint256 cycleEnd = cycleStartTime + CYCLE_DURATION;
        if (block.timestamp >= cycleEnd) return 0;
        return cycleEnd - block.timestamp;
    }
    
    /**
     * @notice Check if account is inactive and burnable
     * @param account Account to check
     * @return true if account can be burned for inactivity
     */
    function isInactive(address account) external view returns (bool) {
        if (balanceOf(account) == 0) return false;
        return block.timestamp >= lastActivity[account] + INACTIVITY_PERIOD;
    }
    
    /**
     * @notice Update activity timestamp on transfers
     * @dev Overrides ERC20 _beforeTokenTransfer hook
     */
    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 amount
    ) internal override {
        super._beforeTokenTransfer(from, to, amount);
        
        // Update activity for sender and receiver
        if (from != address(0)) lastActivity[from] = block.timestamp;
        if (to != address(0)) lastActivity[to] = block.timestamp;
    }
    
    /**
     * @notice Pause all token operations (emergency stop)
     * @dev Only callable by admin
     */
    function pause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _pause();
    }
    
    /**
     * @notice Unpause token operations
     * @dev Only callable by admin
     */
    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _unpause();
    }
}

