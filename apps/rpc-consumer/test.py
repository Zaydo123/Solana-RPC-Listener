import unittest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
import json
import asyncio

# Assuming the functions and classes are imported from your script
from dupe import detect_transactions, swap_callback, RAYDIUM_AMM_ADDRESS

class TestTransactionFunctions(unittest.TestCase):

    def setUp(self):
        self.pre_token_balances = [
            {'accountIndex': 6, 'mint': 'So11111111111111111111111111111111111111112', 'uiTokenAmount': {'uiAmount': '84.194958851', 'decimals': 9, 'amount': '84194958851', 'uiAmountString': '84.194958851'}, 'owner': '5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1', 'programId': 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'}, 
            {'accountIndex': 7, 'mint': '5uKCLQoh9MaELwNT6XkSQALPZoMZ933tLqKKEAXQpump', 'uiTokenAmount': {'uiAmount': '195735793.57244', 'decimals': 6, 'amount': '195735793572440', 'uiAmountString': '195735793.57244'}, 'owner': '5Dj6DgNNKChQQHQLqhNp6jpaXgGyrGcQvLYwQn7RTymV', 'programId': 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'}
        ]

        self.post_token_balances = [
            {'accountIndex': 6, 'mint': 'So11111111111111111111111111111111111111112', 'uiTokenAmount': {'uiAmount': '83.194958851', 'decimals': 9, 'amount': '83194958851', 'uiAmountString': '83.194958851'}, 'owner': '5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1', 'programId': 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'}, 
            {'accountIndex': 7, 'mint': '5uKCLQoh9MaELwNT6XkSQALPZoMZ933tLqKKEAXQpump', 'uiTokenAmount': {'uiAmount': '196735793.57244', 'decimals': 6, 'amount': '196735793572440', 'uiAmountString': '196735793.57244'}, 'owner': '5Dj6DgNNKChQQHQLqhNp6jpaXgGyrGcQvLYwQn7RTymV', 'programId': 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'}
        ]

    def test_detect_transactions(self):
        transactions = detect_transactions(self.pre_token_balances, self.post_token_balances, RAYDIUM_AMM_ADDRESS)
        expected_transactions = [
            {"from": "5Dj6DgNNKChQQHQLqhNp6jpaXgGyrGcQvLYwQn7RTymV", "to": "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1", "amount": 1000000.0, "token": "5uKCLQoh9MaELwNT6XkSQALPZoMZ933tLqKKEAXQpump", "direction": "received"},
            {"from": "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1", "to": "5Dj6DgNNKChQQHQLqhNp6jpaXgGyrGcQvLYwQn7RTymV", "amount": 1.0, "token": "So11111111111111111111111111111111111111112", "direction": "sent"}
        ]
        self.assertCountEqual(transactions, expected_transactions)

    async def test_swap_callback(self):
        ctx = AsyncMock()
        data = json.dumps({
            "result": {
                "value": {
                    "signature": "5NzKrdrdj5p5sTYvGVvEebt4HUgkCmc8pzZjB4AcftmiKpJNh6ozm9GZ1MLQesPtvTkKsD8yuhA7h3H1dnT4vPU9",
                    "err": None,
                    "logs": [
                        "Program log: initialize2",
                        "Program log: other log data"
                    ]
                }
            }
        })

        transaction_data = {
            'result': {
                'meta': {
                    'preTokenBalances': self.pre_token_balances,
                    'postTokenBalances': self.post_token_balances
                },
                'blockTime': 1622543205,
                'transaction': {
                    'message': {
                        'accountKeys': [
                            "So11111111111111111111111111111111111111112",
                            "5uKCLQoh9MaELwNT6XkSQALPZoMZ933tLqKKEAXQpump"
                        ]
                    }
                }
            }
        }

        ctx.get_transaction.return_value.to_json = MagicMock(return_value=json.dumps(transaction_data))

        await swap_callback(ctx, data)

        # Add assertions based on expected behavior of swap_callback
        # Example: Ensure transactions were correctly detected and processed
        ctx.get_transaction.assert_called_once()

if __name__ == '__main__':
    unittest.main()
