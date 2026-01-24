// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.20;

import "forge-std/Script.sol";
import "../src/v2/ConsortiumGovernanceV2.sol";
import "../src/v2/ModelRegistryV2.sol";
import "../src/v2/ComputationVerifierV2.sol";

/**
 * @title Deploy
 * @dev Deployment script for Xcapit FHE-ML Platform contracts.
 *
 * Usage:
 *   # Deploy to local anvil
 *   forge script script/Deploy.s.sol --rpc-url http://localhost:8545 --broadcast
 *
 *   # Deploy to Arbitrum Sepolia (keys from env/vault)
 *   export DEPLOYER_PRIVATE_KEY=$(bao kv get -mount=xcapit blockchain/deployer -field=private_key)
 *   forge script script/Deploy.s.sol \
 *     --rpc-url $ARBITRUM_SEPOLIA_RPC_URL \
 *     --broadcast \
 *     --verify \
 *     --etherscan-api-key $ARBISCAN_API_KEY
 *
 *   # Deploy to Arbitrum mainnet
 *   forge script script/Deploy.s.sol \
 *     --rpc-url $ARBITRUM_RPC_URL \
 *     --broadcast \
 *     --verify \
 *     --etherscan-api-key $ARBISCAN_API_KEY
 */
contract DeployScript is Script {
    // Deployed contract addresses
    ConsortiumGovernanceV2 public governance;
    ModelRegistryV2 public modelRegistry;
    ComputationVerifierV2 public computationVerifier;

    function setUp() public {}

    function run() public {
        // Get deployer private key from environment
        uint256 deployerPrivateKey = vm.envUint("DEPLOYER_PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);

        console.log("Deployer address:", deployer);
        console.log("Deployer balance:", deployer.balance);

        vm.startBroadcast(deployerPrivateKey);

        // Deploy ConsortiumGovernanceV2
        governance = new ConsortiumGovernanceV2();
        console.log("ConsortiumGovernanceV2 deployed at:", address(governance));

        // Deploy ModelRegistryV2
        modelRegistry = new ModelRegistryV2();
        console.log("ModelRegistryV2 deployed at:", address(modelRegistry));

        // Deploy ComputationVerifierV2
        computationVerifier = new ComputationVerifierV2();
        console.log("ComputationVerifierV2 deployed at:", address(computationVerifier));

        vm.stopBroadcast();

        // Log deployment summary
        console.log("\n========== Deployment Summary ==========");
        console.log("Network:", block.chainid);
        console.log("ConsortiumGovernanceV2:", address(governance));
        console.log("ModelRegistryV2:", address(modelRegistry));
        console.log("ComputationVerifierV2:", address(computationVerifier));
        console.log("=========================================\n");

        // Write addresses to file for easy retrieval
        string memory output = string(
            abi.encodePacked(
                '{"network":', vm.toString(block.chainid),
                ',"governance":"', vm.toString(address(governance)),
                '","modelRegistry":"', vm.toString(address(modelRegistry)),
                '","computationVerifier":"', vm.toString(address(computationVerifier)),
                '"}'
            )
        );

        vm.writeFile("deployments.json", output);
        console.log("Addresses written to deployments.json");
    }
}

/**
 * @title DeployTestnet
 * @dev Deployment script specifically for testnets with additional setup.
 */
contract DeployTestnetScript is Script {
    function run() public {
        uint256 deployerPrivateKey = vm.envUint("DEPLOYER_PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);

        // Optional: trusted verifier address from env
        address trustedVerifier = vm.envOr("TRUSTED_VERIFIER_ADDRESS", deployer);

        console.log("Deploying to testnet...");
        console.log("Deployer:", deployer);
        console.log("Trusted verifier:", trustedVerifier);

        vm.startBroadcast(deployerPrivateKey);

        // Deploy contracts
        ConsortiumGovernanceV2 governance = new ConsortiumGovernanceV2();
        ModelRegistryV2 modelRegistry = new ModelRegistryV2();
        ComputationVerifierV2 computationVerifier = new ComputationVerifierV2();

        // Add trusted verifier if different from deployer
        if (trustedVerifier != deployer) {
            modelRegistry.addVerifier(trustedVerifier);
            computationVerifier.addVerifier(trustedVerifier);
            console.log("Added trusted verifier:", trustedVerifier);
        }

        vm.stopBroadcast();

        console.log("\n========== Testnet Deployment ==========");
        console.log("ConsortiumGovernanceV2:", address(governance));
        console.log("ModelRegistryV2:", address(modelRegistry));
        console.log("ComputationVerifierV2:", address(computationVerifier));
        console.log("=========================================\n");
    }
}
