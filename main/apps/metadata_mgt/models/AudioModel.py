from django.db import models
import uuid
from main.apps.metadata_mgt.models.ConversationModel import Conversation

class Audio(models.Model):
    audio_id = models.AutoField(primary_key=True)
    audio_uid = models.UUIDField(default=uuid.uuid4, unique=True)
    audio_path = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    f_conversation_uid = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        to_field='conversation_uid',
        db_column='f_conversation_uid'
    )

    class Meta:
        db_table = 'audio'

    def __str__(self):
        return f"Audio<{self.audio_uid}>"
