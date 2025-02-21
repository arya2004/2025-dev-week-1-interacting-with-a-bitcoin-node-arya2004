from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import json
import time

# Node access params
RPC_URL = "http://alice:password@127.0.0.1:18443"

def send(rpc, addr, message):
    op_return_hex = message.encode("utf-8").hex()
    args = [
        {addr: 100, "data": op_return_hex},  # recipient address and OP_RETURN message
        None,                               # conf target
        None,
        21,                                 # fee rate in sats/vb
        None                                # Empty option object
    ]
    rawtx = rpc.createrawtransaction([], args[0])
    funded = rpc.fundrawtransaction(rawtx, {"feeRate": 0.00021})
    signed = rpc.signrawtransactionwithwallet(funded["hex"])
    txid = rpc.sendrawtransaction(signed["hex"])
    return txid

def list_wallet_dir(rpc):
    result = rpc.listwalletdir()
    return [wallet['name'] for wallet in result['wallets']]

def main():
    rpc = AuthServiceProxy(RPC_URL)

    # Check connection
    info = rpc.getblockchaininfo()
    print(info)

    # Create or load the wallet
    try:
        rpc.createwallet("testwallet")
    except JSONRPCException as e:
        if "already exists" in str(e):
            pass
        else:
            raise

    # Generate a new address
    wallet_rpc = AuthServiceProxy(RPC_URL + "/wallet/testwallet")
    coinbase_address = wallet_rpc.getnewaddress()

    # Mine 101 blocks to the new address to activate the wallet with mined coins
    wallet_rpc.generatetoaddress(101, coinbase_address)
    wallet_rpc.generatetoaddress(100, coinbase_address)

    # Wait for wallet balance update
    time.sleep(1)

    # Prepare a transaction to send 100 BTC with OP_RETURN message
    txid = send(wallet_rpc, "bcrt1qq2yshcmzdlznnpxx258xswqlmqcxjs4dssfxt2", "We are all Satoshi!!")

    # Send the transaction
    print("Broadcasted TXID:", txid)

    # Mine one block to confirm the transaction
    wallet_rpc.generatetoaddress(1, coinbase_address)

    # Write the txid to out.txt
    with open("out.txt", "w") as f:
        f.write(txid)

if __name__ == "__main__":
    main()
