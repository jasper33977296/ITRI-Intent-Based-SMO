from django.db import models
import uuid
from django.utils import timezone
from .UserModel import User


class Agent(models.Model):
    agent_id = models.AutoField(primary_key=True)
    agent_uid = models.UUIDField(default=uuid.uuid4, unique=True)
    agent_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    api_key = models.CharField(max_length=255)
    f_user_uid = models.ForeignKey(
        User,
        to_field='user_uid',
        on_delete=models.CASCADE,
        db_column='f_user_uid'
    )

    class Meta:
        db_table = 'agent'

    def __str__(self):
        return self.agent_name
