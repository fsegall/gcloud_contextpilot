// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../src/CPT.sol";

contract CPTTest is Test {
    CPT public token;
    address public admin;
    address public minter;
    address public burner;
    address public user1;
    address public user2;
    
    function setUp() public {
        admin = address(this);
        minter = makeAddr("minter");
        burner = makeAddr("burner");
        user1 = makeAddr("user1");
        user2 = makeAddr("user2");
        
        // Deploy contract
        token = new CPT();
        
        // Grant roles
        token.grantRole(token.MINTER_ROLE(), minter);
        token.grantRole(token.BURNER_ROLE(), burner);
    }
    
    function testInitialState() public {
        assertEq(token.name(), "Context Pilot Token");
        assertEq(token.symbol(), "CPT");
        assertEq(token.totalSupply(), 0);
        assertEq(token.currentCycleSupply(), 0);
    }
    
    function testMinting() public {
        vm.prank(minter);
        token.mint(user1, 100 ether);
        
        assertEq(token.balanceOf(user1), 100 ether);
        assertEq(token.currentCycleSupply(), 100 ether);
    }
    
    function testMintingWithoutRole() public {
        vm.prank(user1);
        vm.expectRevert();
        token.mint(user2, 100 ether);
    }
    
    function testCycleSupplyLimit() public {
        vm.startPrank(minter);
        
        // Mint up to limit
        token.mint(user1, token.MAX_SUPPLY_PER_CYCLE());
        
        // Try to exceed limit
        vm.expectRevert("CPT: cycle supply limit exceeded");
        token.mint(user2, 1 ether);
        
        vm.stopPrank();
    }
    
    function testInactivityBurn() public {
        // Mint tokens to user1
        vm.prank(minter);
        token.mint(user1, 100 ether);
        
        // Fast forward 30 days + 1 second
        vm.warp(block.timestamp + 30 days + 1);
        
        // Check user is inactive
        assertTrue(token.isInactive(user1));
        
        // Burn inactive account
        vm.prank(burner);
        token.burnInactive(user1);
        
        assertEq(token.balanceOf(user1), 0);
    }
    
    function testCannotBurnActiveAccount() public {
        vm.prank(minter);
        token.mint(user1, 100 ether);
        
        // Try to burn immediately
        vm.prank(burner);
        vm.expectRevert("CPT: account not inactive");
        token.burnInactive(user1);
    }
    
    function testActivityReset() public {
        // Mint to user1
        vm.prank(minter);
        token.mint(user1, 100 ether);
        
        // Fast forward 29 days
        vm.warp(block.timestamp + 29 days);
        
        // User1 transfers (resets activity)
        vm.prank(user1);
        token.transfer(user2, 50 ether);
        
        // Fast forward another 29 days (total 58 days from mint)
        vm.warp(block.timestamp + 29 days);
        
        // User1 should still be active (last activity was 29 days ago)
        assertFalse(token.isInactive(user1));
    }
    
    function testCycleRenewal() public {
        // Mint some tokens
        vm.prank(minter);
        token.mint(user1, 500_000 ether);
        
        assertEq(token.currentCycleSupply(), 500_000 ether);
        
        // Fast forward 30 days
        vm.warp(block.timestamp + 30 days);
        
        // Renew cycle
        token.renewCycle();
        
        // Supply counter should reset
        assertEq(token.currentCycleSupply(), 0);
        
        // Should be able to mint full cycle again
        vm.prank(minter);
        token.mint(user2, token.MAX_SUPPLY_PER_CYCLE());
    }
    
    function testCannotRenewEarly() public {
        vm.warp(block.timestamp + 15 days);
        
        vm.expectRevert("CPT: cycle not ended");
        token.renewCycle();
    }
    
    function testPause() public {
        token.pause();
        
        vm.prank(minter);
        vm.expectRevert("Pausable: paused");
        token.mint(user1, 100 ether);
        
        token.unpause();
        
        vm.prank(minter);
        token.mint(user1, 100 ether);
        assertEq(token.balanceOf(user1), 100 ether);
    }
}

