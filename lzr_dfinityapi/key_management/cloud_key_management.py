import boto3
from decouple import config


class KMSClient:
    def __init__(self, region_name, aws_access_key_id, aws_secret_access_key):
        self.kms_client = boto3.client(
            "kms",
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )

    def encrypt_with_kms(self, ethereum_private_key, key_id):
        response = self.kms_client.encrypt(
            KeyId=key_id, Plaintext=ethereum_private_key
        )
        return response["CiphertextBlob"]

    def decrypt_with_kms(self, encrypted_private_key):
        response = self.kms_client.decrypt(CiphertextBlob=encrypted_private_key)
        return response["Plaintext"]


AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY")
AWS_KMS_KEY_ID = config("AWS_KMS_KEY_ID")
AWS_REGION = "eu-central-1"

kms_client = KMSClient(AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
