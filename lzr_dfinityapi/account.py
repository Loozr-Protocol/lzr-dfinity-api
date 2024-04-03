from ic.identity import Identity
from ic.principal import Principal

from .key_management.encryption import (
    decrypt_from_cipher_string,
    encrypt_private_key_as_string,
)


class Account:
    def __init__(self, encrypted_key="") -> None:
        self.identity = None
        if encrypted_key:
            try:
                private_key = self._decrypt_private_key(encrypted_key)
                self.encrypted_key = encrypted_key
                self.identity = Identity(privkey=private_key)
                self.principal = Principal.self_authenticating(self.identity.pubkey)
            except (ValueError, TypeError):
                pass

        if not self.identity:
            self._create_account()
            self._persist_key(self.identity.privkey)

    def _create_account(self):
        self.identity = Identity()
        self.principal = Principal.self_authenticating(self.identity.pubkey)

    def _persist_key(self, private_key: str):
        self.encrypted_key = encrypt_private_key_as_string(private_key)

    def _decrypt_private_key(self, encrypted_key):
        private_key = decrypt_from_cipher_string(encrypted_key)
        return private_key
