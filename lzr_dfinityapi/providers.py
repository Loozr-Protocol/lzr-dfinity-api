import os
from typing import Type

from ic.agent import Agent
from ic.identity import Identity
from ic.canister import Canister


class CanisterProvider:
    def __init__(self, agent: Agent):
        self._agent = agent

    def load_did(self, candid_name, abi_folder="lzr_dfinityapi/candids"):
        abi_path = os.path.join(abi_folder, f"{candid_name}.did")
        return open(abi_path, "r").read()

    def get_canister(self, canister_id, candid_name) -> Type[Canister]:
        candid = self.load_did(candid_name)
        return Canister(agent=self._agent, canister_id=canister_id, candid=candid)


class BaseCanister(CanisterProvider):
    def __init__(
        self, candid_name: str, canister_id: str, identity: Identity, client=None
    ):
        self.agent = Agent(identity=identity, client=client)
        super().__init__(self.agent)
        self.canister = self.get_canister(canister_id, candid_name)


class TokenCanister(BaseCanister):
    def __init__(
        self,
        identity: Identity,
        canister_id: str,
        client=None,
        candid_name="token_ledger",
    ):
        super().__init__(
            identity=identity,
            candid_name=candid_name,
            canister_id=canister_id,
            client=client,
        )

    def icrc1_symbol(self):
        res = self.canister.icrc1_symbol()
        return res[0]

    def icrc1_metadata(self):
        res = self.canister.icrc1_metadata()
        return res[0]

    def icrc1_decimals(self):
        res = self.canister.icrc1_decimals()
        return res[0]

    def icrc1_fee(self):
        res = self.canister.icrc1_fee()
        return res[0]

    def icrc1_minting_account(self):
        res = self.canister.icrc1_minting_account()
        return res[0]

    def icrc1_name(self):
        res = self.canister.icrc1_name()
        return res[0]

    def icrc1_balance_of(self, principal: str):
        account = {"owner": principal, "subaccount": None}
        res = self.canister.icrc1_balance_of(account)
        return res[0]

    def icrc1_supported_standards(self):
        res = self.canister.icrc1_supported_standards()
        return res[0]

    def icrc1_total_supply(self):
        res = self.canister.icrc1_total_supply()
        return res[0]

    def icrc2_allowance(self, spender_principal: int, principal: str):
        account = {"owner": principal, "subaccount": None}
        spender = {"owner": spender_principal, "subaccount": None}
        res = self.canister.icrc2_allowance(spender=spender, account=account)
        return res[0]

    def icrc1_transfer(self, amount: int, principal: str):
        to = {"owner": principal, "subaccount": None}
        res = self.canister.icrc1_transfer(amount=amount, to=to)
        print("Helloooo:::: ", res)
        # return res[0]

    def icrc2_approve(self, amount: int, principal: str):
        spender = {"owner": principal, "subaccount": None}
        res = self.canister.icrc2_approve(amount=amount, spender=spender)
        print("Helloooo:::: ", res)
        # return res[0]

    def icrc2_transfer_from(self, amount: int, from_principal: str, to_principal: str):
        from_account = {"owner": from_principal, "subaccount": None}
        to_account = {"owner": to_principal, "subaccount": None}
        args = {"amount": amount, "from": from_account, "to": to_account}
        res = self.canister.icrc2_transfer_from(**args)
        print("Helloooo:::: ", res)
        # return res[0]


class CreatorTokenCanister(TokenCanister):
    def __init__(self, identity: Identity, canister_id: str, creator_coin: str, client=None):
        super().__init__(identity, canister_id, client, creator_coin)\
        
    def mint(self, amount: int, principal: str):
        account = {"owner": principal, "subaccount": None}
        res = self.canister.icrc1_transfer(amount=amount, account=account)
        print("Helloooo:::: ", res)
        # return res[0]
    
    def burn(self, amount: int):
        res = self.canister.icrc1_transfer(amount=amount)
        print("Helloooo:::: ", res)
        # return res[0]


class FactoryCanister(BaseCanister):
    def __init__(
        self,
        identity: Identity,
        canister_id: str,
        client=None,
        candid_name="factory_backend",
    ):
        super().__init__(
            identity=identity,
            candid_name=candid_name,
            canister_id=canister_id,
            client=client,
        )

    def new_token(self, name: str, symbol: str) -> str:
        res = self.canister.new_token(name, symbol)
        return res[0]
