# SPPapp/models.py

from django.db import models
from django.contrib.auth.models import User

class StockPrediction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    open_price = models.FloatField()
    high_price = models.FloatField()
    low_price = models.FloatField()
    volume = models.FloatField()
    predicted_price = models.FloatField()
    company = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.company} Prediction on {self.date} by {self.user.username}"
