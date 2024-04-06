from decouple import config


CHAIN_ENV = config("CHAIN_ENV")

ORACLE_IDENTITY = config("ORACLE_IDENTITY")

RPC_URLS = {"development": "http://127.0.0.1:43355", "production": "https://ic0.app"}
RPC_URL = RPC_URLS[CHAIN_ENV or "development"]

FACTORY_CANISTERS = {"development": "", "production": ""}
