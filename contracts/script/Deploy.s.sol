// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/CPT.sol";

contract DeployCPT is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        
        vm.startBroadcast(deployerPrivateKey);
        
        CPT token = new CPT();
        
        console.log("CPT deployed to:", address(token));
        console.log("Deployer address:", vm.addr(deployerPrivateKey));
        
        vm.stopBroadcast();
    }
}

