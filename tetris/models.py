from django.db import models

class TetrisScore(models.Model):
    user_id = models.BigIntegerField()
    chat_id = models.BigIntegerField(null=True, blank=True)
    username = models.CharField(max_length=255, blank=True)
    score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
      indexes = [
          models.Index(fields=["chat_id"]),
          models.Index(fields=["user_id"]),
      ]

    def __str__(self):
        return f"{self.username or self.user_id}: {self.score}"
