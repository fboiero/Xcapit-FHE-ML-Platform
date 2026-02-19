#!/usr/bin/env python3
"""
Transfer testnet ETH on Arbitrum Sepolia.

Usage:
    python scripts/transfer_testnet_eth.py <PRIVATE_KEY> <TO_ADDRESS> [AMOUNT_ETH]

Example:
    python scripts/transfer_testnet_eth.py 0x... 0x27b310c08E94E43b9D3c476BFb1B103b5206a4EF 0.05
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web3 import Web3

# Arbitrum Sepolia RPC
RPC_URL = "https://sepolia-rollup.arbitrum.io/rpc"
CHAIN_ID = 421614

def transfer_eth(private_key: str, to_address: str, amount_eth: float = 0.05):
    """Transfer ETH on Arbitrum Sepolia."""

    # Connect to network
    w3 = Web3(Web3.HTTPProvider(RPC_URL))

    if not w3.is_connected():
        print("❌ Failed to connect to Arbitrum Sepolia")
        return False

    print(f"✅ Connected to Arbitrum Sepolia (chain ID: {CHAIN_ID})")

    # Get account from private key
    account = w3.eth.account.from_key(private_key)
    from_address = account.address

    # Check balance
    balance = w3.eth.get_balance(from_address)
    balance_eth = w3.from_wei(balance, 'ether')
    print(f"📤 From: {from_address}")
    print(f"💰 Balance: {balance_eth:.6f} ETH")

    # Validate recipient
    to_address = Web3.to_checksum_address(to_address)
    print(f"📥 To: {to_address}")
    print(f"💸 Amount: {amount_eth} ETH")

    # Check sufficient balance
    amount_wei = w3.to_wei(amount_eth, 'ether')
    gas_price = w3.eth.gas_price
    gas_limit = 21000  # Standard ETH transfer
    gas_cost = gas_price * gas_limit

    if balance < amount_wei + gas_cost:
        print(f"❌ Insufficient balance. Need {w3.from_wei(amount_wei + gas_cost, 'ether'):.6f} ETH")
        return False

    # Build transaction
    nonce = w3.eth.get_transaction_count(from_address)

    tx = {
        'nonce': nonce,
        'to': to_address,
        'value': amount_wei,
        'gas': gas_limit,
        'gasPrice': gas_price,
        'chainId': CHAIN_ID,
    }

    print(f"\n🔄 Sending transaction...")
    print(f"   Gas price: {w3.from_wei(gas_price, 'gwei'):.2f} gwei")
    print(f"   Gas limit: {gas_limit}")

    # Sign and send
    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    print(f"\n📝 Transaction sent!")
    print(f"   Hash: {tx_hash.hex()}")
    print(f"   Explorer: https://sepolia.arbiscan.io/tx/{tx_hash.hex()}")

    # Wait for confirmation
    print(f"\n⏳ Waiting for confirmation...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

    if receipt['status'] == 1:
        print(f"✅ Transaction confirmed in block {receipt['blockNumber']}")

        # Check new balance of recipient
        new_balance = w3.eth.get_balance(to_address)
        print(f"\n📥 Recipient new balance: {w3.from_wei(new_balance, 'ether'):.6f} ETH")
        return True
    else:
        print(f"❌ Transaction failed")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    private_key = sys.argv[1]
    to_address = sys.argv[2]
    amount = float(sys.argv[3]) if len(sys.argv) > 3 else 0.05

    if not private_key.startswith("0x"):
        private_key = "0x" + private_key

    success = transfer_eth(private_key, to_address, amount)
    sys.exit(0 if success else 1)
