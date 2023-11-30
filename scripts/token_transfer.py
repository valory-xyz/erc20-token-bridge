#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

from web3 import Web3
from eth_account import Account
from web3.middleware import geth_poa_middleware
from ledgereth import get_accounts, create_transaction, sign_transaction
from ledgereth.web3 import LedgerSignerMiddleware
import requests
import json
import os
import binascii
import sys, getopt
import time

from dotenv import load_dotenv

load_dotenv()

ALCHEMY_API_KEY_ETH = os.getenv("ALCHEMY_API_KEY_ETH")
ALCHEMY_API_KEY_POLYGON = os.getenv("ALCHEMY_API_KEY_POLYGON")
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
POLYGONSCAN_API_KEY = os.getenv("POLYGONSCAN_API_KEY")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

# Get the config JSON
with open("config.json") as f:
    config = json.load(f)
# Search for unfinished transfers on L1
from_block_l1 = config['from_block_l1']
from_block_l2 = config['from_block_l2']
# Proof generator URL and message hash topic
proof_generator_url = config['proof_generator_url']
msg_hash_topic = "0x8c5261668696ce22758910d05bab8f186d6eb247ceac2af2e82c7dc17669b036"

w3_l1 = Web3(Web3.HTTPProvider(f"{config['alchemy_url_eth']}{ALCHEMY_API_KEY_ETH}"))
w3_l2 = Web3(Web3.HTTPProvider(f"{config['alchemy_url_polygon']}{ALCHEMY_API_KEY_POLYGON}"))
w3_l2.middleware_onion.inject(geth_poa_middleware, layer=0)
ledger = config['ledger']
account_address = ""

# Get contract ABI
def get_abi(contract_address, url_api, scan_key):
    # Replace 'YourEtherscanApiKey' with your actual Etherscan API key
    url = f"{url_api}/api?module=contract&action=getabi&address={contract_address}&apikey={scan_key}"
    response = requests.get(url)
    data = response.json()
    if data['status'] == '1':
        return json.loads(data['result'])
    else:
        raise ValueError(data['result'])

# Send the tx
def send_tx(message, tx, w3):
    if ledger:
        txn = w3.eth.send_transaction(
            {
                "from": account_address,
                "to": tx['to'],
                "value": tx['value'],
                "gas": tx['gas'],
                "maxPriorityFeePerGas": tx['maxPriorityFeePerGas'],
                "maxFeePerGas": tx['maxFeePerGas'],
                "data": tx['data'],
                "chain_id": tx['chainId']
            }
        )
    else:
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=pk_hex)
        txn = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

    tx_hash = "0x" + binascii.hexlify(txn).decode('utf-8')
    print(f"{message} {tx_hash}")
    result = w3.eth.wait_for_transaction_receipt(txn)

    return tx_hash, result.status

# Check the token allowance and approve, if necessary
def allowance_check_and_approve(contract, w3, token, amount):
    # Check the current allowance
    allowance = int(token.functions.allowance(account_address, contract.address).call())

    if allowance < amount:
        nonce = w3.eth.get_transaction_count(account_address)
        # Approve up to the required allowance
        diff_amount = amount - allowance
        tx = token.functions.approve(contract.address, diff_amount).build_transaction({
            'nonce': nonce
        })

        send_tx("Approve tx:", tx, w3)

# Deposit on L2
def deposit(contract, amount, to_address):
    allowance_check_and_approve(contract, w3_l2, lp_token_contract, amount)

    nonce = w3_l2.eth.get_transaction_count(account_address)
    if to_address == account_address:
        tx = contract.functions.deposit(amount).build_transaction({
            'gas': 200000,
            'nonce': nonce
        })
    else:
        tx = contract.functions.depositTo(to_address, amount).build_transaction({
            'gas': 200000,
            'nonce': nonce
        })

    (tx_hash, status) = send_tx("Deposit on L2 tx (Polygonscan):", tx, w3_l2)
    return tx_hash

# Withdraw from L1
def withdraw(contract, amount, to_address):
    allowance_check_and_approve(contract, w3_l1, bridged_erc20_contract, amount)

    nonce = w3_l1.eth.get_transaction_count(account_address)
    if to_address == account_address:
        tx = contract.functions.withdraw(amount).build_transaction({
            'gas': 200000,
            'nonce': nonce
        })
    else:
        tx = contract.functions.withdrawTo(to_address, amount).build_transaction({
            'gas': 200000,
            'nonce': nonce
        })

    (tx_hash, status) = send_tx("Withdraw on L1 tx (Etherscan):", tx, w3_l1)
    return tx_hash


def receive_message_l1(tx_hash, fx_erc20_root_tunnel_contract, w3):
    url = f"{proof_generator_url}{tx_hash}?eventSignature={msg_hash_topic}"

    try:
        response = requests.get(url)
        data = response.json()

        # Get input data
        if data['message'] == "Payload generation success":
            input_data = data['result']
            # Check if the data hash was already processed, otherwise execute the input tx
            nonce = w3.eth.get_transaction_count(account_address)
            try:
                tx = fx_erc20_root_tunnel_contract.functions.receiveMessage(input_data).build_transaction({
                    'gas': 500000,
                    'nonce': nonce
                })

                print("Processing input data from L2 to L1 tx (Etherscan):", tx_hash)

                (tx_hash, status) = send_tx("Root ERC20 contract to process tokens received on L1 tx (Etherscan):", tx, w3)
                if (status == 1):
                    return True
                else:
                    print("Receive transaction failed on L1 tx (Etherscan)", tx_hash)
                    sys.exit()
            except:
                # Skip already processed tx
                print("Payload processing on L1 failed")
                return False
        return False
    except:
        print(f"Proof generator response API timeout with error: {requests.exceptions}")
        return False

def receive_all_messages_l1(fx_erc20_root_tunnel_contract, fx_erc20_child_tunnel_contract, w3):
    # Get last settled epoch event
    event_filter = fx_erc20_child_tunnel_contract.events.MessageSent.create_filter(fromBlock=from_block_l2, toBlock="latest")
    # Get all entries
    entries = event_filter.get_all_entries()

    # Traverse all entries
    for entry in entries:
        tx_hash = "0x" + binascii.hexlify(entry['transactionHash']).decode("utf-8")
        receive_message(tx_hash, fx_erc20_root_tunnel_contract, w3)


# Distinguish between ledger or regular EOA
if ledger:
    w3_l1.middleware_onion.add(LedgerSignerMiddleware, "ledgereth_middleware")
    w3_l2.middleware_onion.add(LedgerSignerMiddleware, "ledgereth_middleware")
    accounts = get_accounts()
    account = accounts[0]
else:
    account = Account.from_key(PRIVATE_KEY)
    pk_hex = bytearray.fromhex(PRIVATE_KEY)
account_address = account.address

# Get bridge contracts
# lp_token
abi = get_abi(config['abi_lp_token_address'], config['url_api_polygon'], POLYGONSCAN_API_KEY)
lp_token_contract = w3_l2.eth.contract(address=config['lp_token_address'], abi=abi)

# bridged_erc20
abi = get_abi(config['abi_bridged_erc20_address'], config['url_api_eth'], ETHERSCAN_API_KEY)
bridged_erc20_contract = w3_l1.eth.contract(address=config['bridged_erc20_address'], abi=abi)

# fx_erc20_root_tunnel
abi = get_abi(config['abi_fx_erc20_root_tunnel_address'], config['url_api_eth'], ETHERSCAN_API_KEY)
fx_erc20_root_tunnel_contract = w3_l1.eth.contract(address=config['fx_erc20_root_tunnel_address'], abi=abi)

# fx_erc20_root_tunnel
abi = get_abi(config['abi_fx_erc20_child_tunnel_address'], config['url_api_polygon'], POLYGONSCAN_API_KEY)
fx_erc20_child_tunnel_contract = w3_l2.eth.contract(address=config['fx_erc20_child_tunnel_address'], abi=abi)

operation = ""
amount = 0
destination = ""
# Parse command line arguments
opts, args = getopt.getopt(sys.argv[1:], "ho:a:d:", ["operation=","amount=","destination="])
for opt, arg in opts:
    if opt == "-h":
        print("\tUsage: token_transfer.py -o <operation> [-a <amount>(ETH) -d <destination>]")
        print("\n\tExample: token_transfer.py -o deposit -a 1")
        print("\tThis command deposits 1 ether worth of LP token from L2 to L1")
        print("\n\tDefine required environment before running the script:")
        print("\tALCHEMY_API_KEY_ETH, ALCHEMY_API_KEY_POLYGON, ETHERSCAN_API_KEY, POLYGONSCAN_API_KEY, [PRIVATE_KEY]")
        print("\n\tLedger note: This version of the script uses the default ledger derivation path (accounts[0])")
        print("\tModify the code to account for your ledger derivation path, if needed")
        sys.exit()
    elif opt in ("-o", "--operation"):
        operation = arg
    elif opt in ("-a", "--amount"):
        amount = int(float(arg) * 10**18)
    elif opt in ("-d", "--destination"):
        destination = arg

print("Account address:", account_address)

# Deposit
if operation == "deposit":
    if amount > 0:
        balance = lp_token_contract.functions.balanceOf(account_address).call()
        print("Account balance:", balance)
        if (balance < amount):
            print("Insufficient balance")
            sys.exit()
        if (destination == ""):
            tx_hash = deposit(fx_erc20_child_tunnel_contract, amount, account_address)
        else:
            tx_hash = deposit(fx_erc20_child_tunnel_contract, amount, destination)

        # Wait for the proofs to finalize tx on L1
        while True:
            result = receive_message_l1(tx_hash, fx_erc20_root_tunnel_contract, w3_l1)
            if not result:
                print("Waiting for the proofs to finalize tx on L1. Next check in 5 minutes...")
                time.sleep(300)
            else:
                break
        print("Deposit has been completed")
    else:
        print("Amount is incorrect")
        sys.exit()

# Withdraw
elif operation == "withdraw":
    if amount > 0:
        balance = bridged_erc20_contract.functions.balanceOf(account_address).call()
        print("Account balance:", balance)
        if (balance < amount):
            print("Insufficient balance")
            sys.exit()
        if (destination == ""):
            withdraw(fx_erc20_root_tunnel_contract, amount, account_address)
        else:
            withdraw(fx_erc20_root_tunnel_contract, amount, destination)
    else:
        print("Amount is incorrect")
        sys.exit()

# Output balances
elif operation == "balances":
    balance = lp_token_contract.functions.balanceOf(account_address).call()
    print("Balance of LP token on Polygon:", balance)
    balance = bridged_erc20_contract.functions.balanceOf(account_address).call()
    print("Balance of bridged token on Ethereum:", balance)

# Finalize deposits on L1
elif operation == "finalize_l1_deposits":
    receive_all_messages_l1(fx_erc20_root_tunnel_contract, fx_erc20_child_tunnel_contract, w3_l1)

# Undefined operation, output help
else:
    print("\tUsage: token_transfer.py -o <operation> [-a <amount>(ETH) -d <destination>]")
    print("\tExample: token_transfer.py -o deposit -a 1")
    print("\tThis command deposits 1 ether worth of LP token from L2 to L1")
    print("\n\tDefine required environment before running the script:")
    print("\tALCHEMY_API_KEY_ETH, ALCHEMY_API_KEY_POLYGON, ETHERSCAN_API_KEY, POLYGONSCAN_API_KEY, [PRIVATE_KEY]")
    print("\n\tLedger note: This version of the script uses the default ledger derivation path (accounts[0])")
    print("\tModify the code to account for your ledger derivation path, if needed")
    sys.exit()
