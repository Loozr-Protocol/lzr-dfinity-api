from django.db import models
from django.conf import settings


USER_MODEL = getattr(settings, "AUTH_USER_MODEL", None) or "auth.User"
BOUGHT = "BOUGHT"
SOLD = "SOLD"
TX_TYPE_CHOICES = [
    (BOUGHT, BOUGHT),
    (SOLD, SOLD),
]


class BaseModelMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ("-created_at",)


class Coin(BaseModelMixin):
    canister_id = models.CharField(max_length=300)
    creator = models.ForeignKey(USER_MODEL, on_delete=models.CASCADE)
    total_supply = models.DecimalField(max_digits=50, decimal_places=0, default=0)
    reserve_balance = models.DecimalField(max_digits=50, decimal_places=0, default=0)
    symbol = models.CharField(max_length=10)
    name = models.CharField(max_length=50)
    holders = models.ManyToManyField("Holder", related_name="coin_holders")


class Holder(BaseModelMixin):
    user = models.ForeignKey(USER_MODEL, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=50, decimal_places=0, default=0)
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)


class Log(BaseModelMixin):
    user = models.ForeignKey(USER_MODEL, on_delete=models.CASCADE)
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    tx_type = models.CharField(max_length=100, choices=TX_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=50, decimal_places=0, default=0)
