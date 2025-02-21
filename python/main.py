from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import time


class BitcoinWallet:
    """Handles wallet-related operations like creation, address generation, and mining."""

    def __init__(self, rpc_url, wallet_name="testwallet"):
        """
        initializes Bitcoin wallet connection
        :param rpc_url: RPC connection URL
        :param wallet_name: Name of the wallet to use/create
        """
        self.rpc_url = rpc_url
        self.wallet_name = wallet_name
        self.rpc = AuthServiceProxy(rpc_url)  # main rpc connection
        self.wallet_rpc = None  # wallet-specific rpc, will be set after loading wallet

    def create_or_load_wallet(self):
        """Creates a new wallet if it doesn't exist, otherwise loads it."""
        try:
            self.rpc.createwallet(self.wallet_name)
        except JSONRPCException as e:
            if "already exists" in str(e):
                print(f"wallet '{self.wallet_name}' already exists, loading it...")
            else:
                raise  # some other error, don't suppress it

        # connect to the wallet
        self.wallet_rpc = AuthServiceProxy(f"{self.rpc_url}/wallet/{self.wallet_name}")

    def generate_new_address(self):
        """Generates a new Bitcoin address from the wallet."""
        if not self.wallet_rpc:
            raise Exception("wallet not initialized. call create_or_load_wallet() first.")
        return self.wallet_rpc.getnewaddress()

    def mine_blocks(self, num_blocks, address):
        """
        Mines `num_blocks` to the given address (only works on regtest mode).
        :param num_blocks: Number of blocks to mine
        :param address: Address to receive mining rewards
        """
        if not self.wallet_rpc:
            raise Exception("wallet not initialized. call create_or_load_wallet() first.")
        self.wallet_rpc.generatetoaddress(num_blocks, address)

    def get_wallet_rpc(self):
        """Returns the wallet-specific RPC connection."""
        if not self.wallet_rpc:
            raise Exception("wallet not initialized. call create_or_load_wallet() first.")
        return self.wallet_rpc


class BitcoinTransaction:
    """Handles Bitcoin transactions including sending BTC and embedding OP_RETURN messages."""

    def __init__(self, wallet_rpc):
        """
        initializes transaction handler
        :param wallet_rpc: AuthServiceProxy object connected to a specific wallet
        """
        self.wallet_rpc = wallet_rpc

    def send(self, recipient_address, message, amount=100, fee_rate=0.00021):
        """
        creates & sends a Bitcoin transaction with an OP_RETURN message
        :param recipient_address: Address to send BTC to
        :param message: Message to store in blockchain
        :param amount: BTC amount to send (default 100 BTC)
        :param fee_rate: Transaction fee rate in BTC/kvB (default 0.00021)
        :return: Transaction ID
        """

        # convert msg to hex (needed for OP_RETURN)
        op_return_hex = message.encode("utf-8").hex()

        # define tx outputs - send btc + embed OP_RETURN msg
        outputs = [{recipient_address: amount, "data": op_return_hex}]

        # create raw transaction
        raw_tx = self.wallet_rpc.createrawtransaction([], outputs[0])

        # fund tx using available balance
        funded_tx = self.wallet_rpc.fundrawtransaction(raw_tx, {"feeRate": fee_rate})

        # sign tx
        signed_tx = self.wallet_rpc.signrawtransactionwithwallet(funded_tx["hex"])

        # broadcast tx
        txid = self.wallet_rpc.sendrawtransaction(signed_tx["hex"])

        return txid


def main():
    """Main function - sets up wallet, mines coins, and sends a transaction."""

    # rpc connection url
    RPC_URL = "http://alice:password@127.0.0.1:18443"

    # initialize wallet handler
    wallet = BitcoinWallet(RPC_URL)

    # create/load wallet
    wallet.create_or_load_wallet()

    # generate a new address for mining rewards
    miner_address = wallet.generate_new_address()

    # mine 101 blocks (needed to unlock mining rewards)
    wallet.mine_blocks(101, miner_address)

    # mine additional blocks for more balance
    wallet.mine_blocks(100, miner_address)

    # wait a bit for wallet to update balance
    time.sleep(1)

    # initialize transaction handler using the wallet rpc
    tx_handler = BitcoinTransaction(wallet.get_wallet_rpc())

    # define recipient & message
    recipient_address = "bcrt1qq2yshcmzdlznnpxx258xswqlmqcxjs4dssfxt2"
    message = "We are all Satoshi!!"

    # send transaction with OP_RETURN message
    txid = tx_handler.send(recipient_address, message)

    # print tx id
    print("broadcasted txid:", txid)

    # mine 1 block to confirm transaction
    wallet.mine_blocks(1, miner_address)

    # save tx id to file
    with open("out.txt", "w") as file:
        file.write(txid)


# run script only if executed directly
if __name__ == "__main__":
    main()
