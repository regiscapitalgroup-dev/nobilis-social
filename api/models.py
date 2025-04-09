from django.db import models

# Create your models here.
class InviteTmpToken(models.Model):
    user_email = models.EmailField(max_length=255, primary_key=True, unique=True)
    user_token = models.TextField()
    user_id = models.IntegerField(default=0)

    def __str__(self):
        return self.user_email
