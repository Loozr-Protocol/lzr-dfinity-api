from typing import Union

from django.db import transaction
from django.db.models import F
from ic import Identity
from ic.client import Client
from web3 import Web3
from web3.types import Wei

from .providers import CreatorTokenCanister, FactoryCanister
from .models import BOUGHT, SOLD, Coin, Log, Holder
from .config import RPC_URL, CHAIN_ENV, FACTORY_CANISTERS, ORACLE_IDENTITY


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
    def _calc_polynomial_target_amount(
        cls, x: Union[int, float], p: Union[int, float]
    ):
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
        factory_canister_id = FACTORY_CANISTERS[CHAIN_ENV]
        oracle_id = Identity(privkey=ORACLE_IDENTITY)
        factory_canister = FactoryCanister(
            identity=oracle_id, client=client, canister_id=factory_canister_id
        )
        result = factory_canister.new_token(name, symbol)

        coin.canister_id = result
        coin.save()

        return coin


def buy_coin(user, coin: Coin, lzr_amount: Union[int, float]):
    mint_amount = ContinuosToken.calc_purchase_return(
        coin.total_supply, coin.reserve_balance, lzr_amount
    )
    client = Client(url=RPC_URL)
    canister_id = coin.canister_id
    oracle_id = Identity(privkey=ORACLE_IDENTITY)
    coin_canister = CreatorTokenCanister(
        identity=oracle_id, client=client, canister_id=canister_id
    )

    mint_amount_wei = Web3.to_wei(mint_amount)
    user_principal = user.account_principal

    coin_canister.mint(mint_amount_wei, user_principal)

    Log.objects.create(user=user, coin=coin, amount=int(mint_amount_wei), tx_type=BOUGHT)
    try:
        coin_balance_record = Holder.objects.get(user=user.pk, coin=coin.pk)
    except Holder.DoesNotExist:
        coin_balance_record = Holder.object.create(user=user, coin=coin)

    coin_balance_record.balance = F("balance") + int(mint_amount_wei)
    coin_balance_record.save()

    coin_balance_record.refresh_from_db()


def sell_coin(user, user_identity: Identity, coin: Coin, coin_amount: Union[int, float]) -> Wei:
    burn_amount = ContinuosToken.calc_sale_return(
        coin.total_supply, coin.reserve_balance, coin_amount
    )
    burn_amount_wei = Web3.to_wei(burn_amount)

    try:
        coin_balance_record = Holder.objects.get(user=user.pk, coin=coin.pk)
    except Holder.DoesNotExist:
        raise ValueError("You do not have any token to sell")
    
    if coin_balance_record.balance < int(burn_amount_wei):
        raise ValueError("You do not have enough token to sell")

    client = Client(url=RPC_URL)
    canister_id = coin.canister_id
    coin_canister = CreatorTokenCanister(
        identity=user_identity, client=client, canister_id=canister_id
    )

    coin_canister.burn(burn_amount_wei)

    Log.objects.create(user=user, coin=coin, amount=int(burn_amount_wei), tx_type=SOLD)
    
    coin_balance_record.balance = F("balance") - int(burn_amount_wei)
    coin_balance_record.save()

    coin_balance_record.refresh_from_db()

    return burn_amount_wei


def get_holders(coin_id: int):
    return Holder.objects.filter(coin=coin_id)


def get_holder_record(coin_id: int, user_id: int):
    return Holder.objects.get(coin=coin_id, user=user_id)


def get_user_holdings(user_id):
    return Holder.objects.filter(user=user_id)
