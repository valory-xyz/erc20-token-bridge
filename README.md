# erc20-token-bridge
ERC20 tokens cross-chain bridging scripts.

## Introduction
This repository contains the scripts and configuration for L1-L2 networks to facilitate in bridging tokens from L2 to L1
and vice versa.

The code is written on Python 3.10.

Current implementation provides CLI workflow to deposit and withdraw tokens between Polygon and Ethereum networks.
During deposit, a specified amount of tokens will be locked on a Polygon bridge contract, and a corresponding amount of
bridged tokens will be minted on Ethereum side. In case of withdraw, a specified amount of bridged tokens will be
burnt on Ethereum, and a corresponding amount of original tokens will be released (transferred) on Polygon.

## Configuration
Depending on testnet or mainnet usage, the configuration is written in their corresponding files:
- `scripts/polygon-eth/config_mainnet.json`
- `scripts/polygon-eth/config_testnet.json`

Before running the script, copy one of the specified configuration files into `config.json`, or create one with own set
of contract addresses.

Note that following environment variables need to be exported in order to run the script:
- `ALCHEMY_API_KEY_ETH`, `ALCHEMY_API_KEY_POLYGON`: alchemy API keys for networks
- `ETHERSCAN_API_KEY`, `POLYGONSCAN_API_KEY`: scan keys for networks
- `PRIVATE_KEY`: wallet private key, if regular EOA is used (not ledger)

## CLI options and examples
### Helper
```
python3 token_transfer.py -h
```

### Check balances on both chains
```
python3 token_transfer.py -o balances
```

The output will be similar to the following one:
```
Account address: 0xXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXx
LP token balance on Polygon: 1000000.0
Bridged token balance on Ethereum: 0.0
```

### Deposit tokens from Polygon to Ethereum where the receiver address matches the sender one
Required parameters:
- `-o deposit`: deposit operation;
- `-a amount_tokens`: amount of tokens in ether value.

Example:
```
python3 token_transfer.py -o deposit -a 1000
```

The output will be similar to the following one:
```
Account address: 0xXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXx
Token balance on Polygon: 999000.0
Approve tx: 0xaf32bbd11c40747f56f7a9b8ddbfffcd835105020fa4efee8b10e6ab3f8e643d
Deposit on L2 tx (Polygonscan): 0x58d0a0480a029b82281440e5e3ae13095f65462b42cbbd684a26040ef674b3d5
Waiting for the proofs to finalize tx on L1. Next check is in 5 minutes...
...
Waiting for the proofs to finalize tx on L1. Next check is in 5 minutes...

```

### Deposit tokens from Polygon to Ethereum where the receiver address is different from the sender one
Required parameters:
- `-o deposit`: deposit operation;
- `-a amount_tokens`: amount of tokens in ether value;
- `-d destination_address`: Destination address.

Example:
```
python3 token_transfer.py -o deposit -a 1000 -d 0xYyYyYyYyYyYyYyYyYyYyYyYyYyYyYyYyYyYyYyYy
```

The output will be similar to the following one:
```
Account address: 0xXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXx
Token balance on Polygon: 1000000.0
Approve tx: 0xc2ccf698668921f18f17bdaf121650806031e700b2c43ec88007ecedbb9f327b
Deposit on L2 tx (Polygonscan): 0xd5b3cbdf55a0419f5f96551545661b14e563f9874520561c1a9e261672ea7906
Waiting for the proofs to finalize tx on L1. Next check is in 5 minutes...
...
Waiting for the proofs to finalize tx on L1. Next check is in 5 minutes...
Processing input data from L2 to L1 tx (Polygonscan): 0xd5b3cbdf55a0419f5f96551545661b14e563f9874520561c1a9e261672ea7906
Root ERC20 contract to process tokens received on L1 tx (Etherscan): 0x5499f827cd8e23fbdf70cba920cb88f7a6ee67483d273310cd45d8038a36d422
Deposit has been completed
```

### Withdraw tokens from Ethereum to Polygon where the receiver address matches the sender one
Required parameters:
- `-o withdraw`: withdraw operation;
- `-a amount_tokens`: amount of tokens in ether value.

Example:
```
python3 token_transfer.py -o withdraw -a 500
```

The output will be similar to the following one:
```
Account address: 0xXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXx
Bridged token balance on Ethereum: 1000.0
Approve tx: 0x949673d53c8b8afadae90896eccb9913f448580ec80e0722fcd4961c88ce464a
Withdraw on L1 tx (Etherscan): 0x47d2ed89c2396b68cee1c100b39b4b4ec5833ed675bd69fa08fac3982fd780f0
Withdraw has been initiated, check balances in about half an hour or more
```


### Withdraw tokens from Ethereum to Polygon where the receiver address is different from the sender one
Required parameters:
- `-o withdraw`: withdraw operation;
- `-a amount_tokens`: amount of tokens in ether value;
- `-d destination_address`: Destination address.

Example:
```
python3 token_transfer.py -o withdraw -a 500 -d 0xYyYyYyYyYyYyYyYyYyYyYyYyYyYyYyYyYyYyYyYy
```

The output will be similar to the following one:
```
Account address: 0xXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXx
Bridged token balance on Ethereum: 500.0
Approve tx: 0x9c3d3613bca834e52775bb300371e5e3dbc29f0fdfd550775d8a8cacfe32f5db
Withdraw on L1 tx (Etherscan): 0x8df271859a812aab13c575aa928f11bdee51899dbf23b2b9472d6f085689b297
Withdraw has been initiated, check balances in about half an hour or more
```

### Finalize L1 deposits
This command is useful if L1 deposits were not complete or if the script got interrupted.

Required parameters:
- `-o finalize_l1_deposits`: finalize L1 deposits operation.

Example:
```
python3 token_transfer.py -o finalize_l1_deposits
```

The output will be similar to the following one:
```
Account address: 0xXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXx

```