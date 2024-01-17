# erc20-token-bridge
Script to bridge [50WMATIC-50OLAS](https://polygonscan.com/address/0x62309056c759c36879cde93693e7903bf415e4bc) from Polygon POS to Ethereum, and vice versa.

## Introduction
This repository contains the scripts and configuration to facilitate bridging the [50WMATIC-50OLAS](https://polygonscan.com/address/0x62309056c759c36879cde93693e7903bf415e4bc) token between Polygon POS and Ethereum.

The code is written in Python 3.10.

Current implementation provides CLI workflow to deposit and withdraw tokens between Polygon and Ethereum networks.
During deposit, a specified amount of tokens will be locked on a [Polygon bridge contract](https://polygonscan.com/address/0x1fe74A08ac89300B102AdCd474C721AE8764E850), and a corresponding amount of [bridged tokens](https://etherscan.io/address/0x06512E620A8317da51a73690A596Aca97287b31D) will be minted on the Ethereum side. In case of withdraw, a specified amount of bridged tokens will be burnt by [a bridge contract on Ethereum](https://etherscan.io/address/0x1737408def992AF04b29C8Ba4BBcD7397B08c930), and a corresponding amount of original tokens will be released (transferred) on Polygon.

## Configuration
Depending on testnets (Goerli<>Mumbai) or mainnet (Ethereum<>Polygon) usage, the configuration is written in their corresponding files:
- `scripts/polygon-eth/config_mainnet.json`
- `scripts/polygon-eth/config_testnet.json`

Before running the script, copy one of the specified configuration files into `config.json`.

Also, copy the environment variables template:
```
cp .example.env .env
```

Note that following environment variables need to be provided in order to run the script:
- `ALCHEMY_API_KEY_ETH`, `ALCHEMY_API_KEY_POLYGON`: alchemy API keys for networks
- `ETHERSCAN_API_KEY`, `POLYGONSCAN_API_KEY`: scan keys for networks

Also, either use a private key from environment variable by exporting:
-  `PRIVATE_KEY`: wallet private key, if regular EOA is used (not ledger)
Or, use a hardware wallet, and configure `"ledger": true`  in `config.json`. By default the `account_index` is set to zero, configure if required.

## Installation

It is assumed you have installed [Poetry](https://python-poetry.org/). Install dependencies by running:
```
poetry install
```

## CLI options and examples
### Helper
```
poetry run scripts/polygon-eth/token_transfer.py -h
```

### Check balances on both chains
```
poetry run scripts/polygon-eth/token_transfer.py -o balances
```

The output will be similar to the following one:
```
Account address: 0xXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXx
Token balance on Polygon: 1000000.0
Bridged token balance on Ethereum: 0.0
```

### Deposit tokens from Polygon to Ethereum where the receiver address matches the sender one
Required parameters:
- `-o deposit`: deposit operation;
- `-a amount_tokens`: amount of tokens in ether value.

Example:
```
poetry run scripts/polygon-eth/token_transfer.py -o deposit -a 1
```

The output will be similar to the following one:
```
Account address: 0xXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXx
Token balance on Polygon: 1.0
Approval tx for amount '1.0' and spender '0x1fe74A08ac89300B102AdCd474C721AE8764E850':
{
    ...
}
Sign on your ledger now ...
Approve tx: 0xaf32bbd11c40747f56f7a9b8ddbfffcd835105020fa4efee8b10e6ab3f8e643d
Bridging tx for amount '1.0' and Ethereum address receiver '0xXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXx':
{
    ...
}
Sign on your ledger now ...
Deposit on L2 tx (Polygonscan): 0x58d0a0480a029b82281440e5e3ae13095f65462b42cbbd684a26040ef674b3d5
Waiting for the proofs to finalize tx on L1. Next check is in 5 minutes...
...
Waiting for the proofs to finalize tx on L1. Next check is in 5 minutes...
Processing input data from L2 to L1 tx (Polygonscan): 0x58d0a0480a029b82281440e5e3ae13095f65462b42cbbd684a26040ef674b3d5
Root ERC20 contract to process tokens received on L1 tx (Etherscan): 0xe033a925bac7ac478db4e7ddd646b3aa9bf913afca576b0bf0aa715cfed54994
Deposit has been completed
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
Token balance on Polygon: 1000.0
Approval tx for amount '1000.0' and spender '0x1fe74A08ac89300B102AdCd474C721AE8764E850':
{
    ...
}
Sign on your ledger now ...
Approve tx: 0xc2ccf698668921f18f17bdaf121650806031e700b2c43ec88007ecedbb9f327b
Bridging tx for amount '1000.0' and Ethereum address receiver '0xYyYyYyYyYyYyYyYyYyYyYyYyYyYyYyYyYyYyYyYy':
{
    ...
}
Sign on your ledger now ...
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
Finalizing outstanding L1 deposits
Processing input data from L2 to L1 tx (Polygonscan): 0x63c4b4243c20647bb5e82c746f360b8a336ed9f42a9b319042d39ba320d9aa65
Root ERC20 contract to process tokens received on L1 tx (Etherscan): 0x359a58abea49219b88d4d55abbb27e0fa6b09ab6712d74f4ffd7d28c6de888d2
```
