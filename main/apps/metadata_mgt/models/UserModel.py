from django.db import models
from django.utils import timezone
import uuid

class User(models.Model):
    user_id = models.AutoField(primary_key=True) 
    user_uid = models.UUIDField(default=uuid.uuid4, unique=True)
    user_uname = models.CharField(max_length=50,unique=True)
    user_password = models.CharField(max_length=255)
    user_role = models.CharField(max_length=50, blank=True, null=True)
    user_uemail = models.CharField(max_length=255, unique=True)
    created_time = models.DateTimeField(default=timezone.now)
    last_login_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'user'

    def __str__(self):
        return self.user_uname
