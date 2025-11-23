from django.db import models


class TetrisScore(models.Model):
    user_id = models.BigIntegerField()
    chat_id = models.BigIntegerField()
    username = models.CharField(max_length=255, blank=True, null=True)
    best_score = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user_id", "chat_id")

    def __str__(self):
        return f"{self.username or self.user_id} - {self.best_score}"
