from typing import Union

from django.db import transaction
from django.db.models import F
from ic import Identity
from ic.client import Client
from web3 import Web3
from web3.types import Wei
from ic.agent import Agent
from ic.candid import encode, Types

from .providers import CreatorTokenCanister
from .models import BOUGHT, SOLD, Coin, Log, Holder
from .config import RPC_URL, FACTORY_CANISTER, ORACLE_IDENTITY


class ContinuosToken:
    r = 0.3333  # reserve ratio 1/3
    m = 0.003  # slope
    increment_rate = 3  # (n+1)

    @classmethod
    def _calc_bancor_target_amount(
        cls, x: Union[int, float], rb: Union[int, float], p: Union[int, float]
    ):
        """This is the formula: `x * ((1 + p / rb) ^ (r) - 1)`"""
        if x < 1 or rb < 1:
            raise ValueError("Incorrect input parameter")

        if p == 0:
            return 0

        # ((((p + rb) / rb) ** r) * x) - x
        term1 = (p + rb) / rb
        term2 = term1**cls.r
        term3 = term2 * x

        return term3 - x

    @classmethod
    def _calc_polynomial_target_amount(cls, x: Union[int, float], p: Union[int, float]):
        """
        This is the formula: `(((((3*p)/m) + (x^3)) ^ r) - x)`

        "3" here is n + 1, n is the rate of increase
        """
        if p == 0:
            return 0

        # this is the same as (((n+1) * p) / m) + x ^ (n+1)
        term1 = 1000 * p + x**cls.increment_rate
        term2 = term1**cls.r
        term3 = term2 - x

        return term3

    @classmethod
    def calc_sale_return(
        cls, x: Union[int, float], rb: Union[int, float], p: Union[int, float]
    ):
        if x < 1 or rb < 1 or p > x:
            raise ValueError("Incorrect input parameter")

        if p == 0:
            return 0

        # special case for selling the entire supply
        if p == x:
            return rb

        term1 = 1 - p / x
        term2 = 1 / cls.r
        term3 = term1**term2
        term4 = rb * (1 - term3)

        return term4

    @classmethod
    def calc_purchase_return(
        cls, x: Union[int, float], rb: Union[int, float], p: Union[int, float]
    ):
        if x == 0:
            return cls._calc_polynomial_target_amount(x, p)

        return cls._calc_bancor_target_amount(x, rb, p)


def create_coin(user, symbol: str, name: str) -> Coin:
    with transaction.atomic():
        if Coin.objects.filter(name=name).exists():
            raise ValueError("Token already exists!")
        coin = Coin.objects.create(name=name, symbol=symbol, creator=user)

        client = Client(url=RPC_URL)
        factory_canister_id = FACTORY_CANISTER
        oracle_id = Identity(privkey=ORACLE_IDENTITY)
        agent = Agent(identity=oracle_id, client=client)

        params = [
            {"type": Types.Text, "value": name},
            {"type": Types.Text, "value": symbol},
        ]
        result = agent.update_raw(factory_canister_id, "new_token", encode(params))

        coin.canister_id = result[0]["value"]
        coin.save()

        return coin


def buy_coin(user, coin: Coin, lzr_amount: Union[int, float]):
    with transaction.atomic():
        coin_reserve_balance = float(Web3.from_wei(coin.reserve_balance, "ether"))
        coin_total_supply = float(Web3.from_wei(coin.total_supply, "ether"))

        mint_amount = ContinuosToken.calc_purchase_return(
            coin_total_supply, coin_reserve_balance, lzr_amount
        )

        mint_amount_wei = Web3.to_wei(mint_amount, "ether")
        user_principal = user.account_principal

        Log.objects.create(
            user=user, coin=coin, amount=int(mint_amount_wei), tx_type=BOUGHT
        )
        try:
            coin_balance_record = Holder.objects.get(user=user.pk, coin=coin.pk)
        except Holder.DoesNotExist:
            coin_balance_record = Holder.objects.create(user=user, coin=coin)

        coin_balance_record.balance = F("balance") + int(mint_amount_wei)
        coin_balance_record.save()

        coin.reserve_balance = F("reserve_balance") + int(Web3.to_wei(lzr_amount, "ether"))
        coin.total_supply = F("total_supply") + int(Web3.to_wei(mint_amount, "ether"))
        coin.holders.add(coin_balance_record)

        coin.save()

        coin_balance_record.refresh_from_db()

        client = Client(url=RPC_URL)
        canister_id = coin.canister_id
        oracle_id = Identity(privkey=ORACLE_IDENTITY)
        coin_canister = CreatorTokenCanister(
            identity=oracle_id,
            client=client,
            canister_id=canister_id,
            creator_coin="lzr_founder_coin_backend",
        )

        coin_canister.mint(mint_amount_wei, user_principal)


def sell_coin(
    user, user_identity: Identity, coin: Coin, coin_amount: Union[int, float]
) -> Wei:
    with transaction.atomic():
        coin_reserve_balance = float(Web3.from_wei(coin.reserve_balance, "ether"))
        coin_total_supply = float(Web3.from_wei(coin.total_supply, "ether"))

        burn_amount = ContinuosToken.calc_sale_return(
            coin_total_supply, coin_reserve_balance, coin_amount
        )
        burn_amount_wei = Web3.to_wei(burn_amount, "ether")

        try:
            coin_balance_record = Holder.objects.get(user=user.pk, coin=coin.pk)
        except Holder.DoesNotExist:
            raise ValueError("You do not have any token to sell")

        if coin_balance_record.balance < int(burn_amount_wei):
            raise ValueError("You do not have enough token to sell")
        
        Log.objects.create(
            user=user,
            coin=coin,
            amount=int(Web3.to_wei(coin_amount, "ether")),
            tx_type=SOLD,
        )

        coin_balance_record.balance = F("balance") - int(Web3.to_wei(coin_amount, "ether"))
        coin_balance_record.save()

        coin.reserve_balance = F("reserve_balance") - int(Web3.to_wei(burn_amount, "ether"))
        coin.total_supply = F("total_supply") - int(Web3.to_wei(coin_amount, "ether"))

        coin.save()

        coin_balance_record.refresh_from_db()

        client = Client(url=RPC_URL)
        canister_id = coin.canister_id
        coin_canister = CreatorTokenCanister(
            identity=user_identity,
            client=client,
            canister_id=canister_id,
            creator_coin="lzr_founder_coin_backend",
        )

        coin_canister.burn(burn_amount_wei)

        return burn_amount_wei


def get_holders(coin_id: int):
    return Holder.objects.filter(coin=coin_id, balance__gt=0)


def get_holder_record(coin_id: int, user_id: int):
    return Holder.objects.get(coin=coin_id, user=user_id, balance__gt=0)


def get_user_holdings(user_id):
    return Holder.objects.filter(user=user_id, balance__gt=0)
