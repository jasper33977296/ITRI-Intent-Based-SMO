import uuid
from django.db import models
from django.utils import timezone
from main.apps.metadata_mgt.models.ConversationModel import Conversation

class Workflow(models.Model):
    """
    一對一 (OneToOneField)：
      - 同一個 Conversation 只能對應一個 Workflow
      - workflow_id: 自增量主鍵，純內部使用即可
      - f_conversation_uid: OneToOne 對應到 conversation_uid
    """
    workflow_id = models.AutoField(primary_key=True)

    workflow_step = models.CharField(max_length=50)
    workflow_status = models.CharField(max_length=255)

    start_time = models.DateTimeField(default=timezone.now, blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)

    f_conversation_uid = models.OneToOneField(
        Conversation,
        to_field='conversation_uid',
        on_delete=models.CASCADE,
        db_column='f_conversation_uid',
        related_name='workflow',
        unique=True
    )

    class Meta:
        db_table = 'workflow'

    def __str__(self):
        return f'[Workflow] ID={self.workflow_id}, Step={self.workflow_step}'
