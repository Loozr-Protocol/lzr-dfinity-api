from decouple import config


CHAIN_ENV = config("CHAIN_ENV")
DEVELOPMENT_RPC = config("DEVELOPMENT_RPC")
ORACLE_IDENTITY = config("ORACLE_IDENTITY")

RPC_URLS = {"development": DEVELOPMENT_RPC or "http://127.0.0.1:33239", "production": "https://ic0.app"}
RPC_URL = RPC_URLS[CHAIN_ENV or "development"]

FACTORY_CANISTER = config("FACTORY_CANISTER")

CANDID_FOLDER = config("CANDID_FOLDER")
