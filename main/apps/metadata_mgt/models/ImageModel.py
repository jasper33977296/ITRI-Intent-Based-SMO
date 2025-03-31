from django.db import models
import uuid

from main.apps.metadata_mgt.models.TextModel import Text
from main.apps.metadata_mgt.models.ConversationModel import Conversation

class Image(models.Model):
    # Primary key: Auto-increment integer
    image_id = models.AutoField(primary_key=True)

    # Globally unique identifier, auto-generated
    image_uid = models.UUIDField(default=uuid.uuid4, unique=True)

    # Path or filename to the image; adjust length to suit your needs
    image_path = models.CharField(max_length=255)

    # Time of creation, automatically set on record creation
    created_at = models.DateTimeField(auto_now_add=True)

    # Foreign key referencing Text.text_uid
    f_text_uid = models.ForeignKey(
        Text,
        on_delete=models.CASCADE,
        to_field='text_uid',  
        db_column='f_text_uid'
    )

    # Foreign key referencing Conversation.conversation_uid
    f_conversation_uid = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        to_field='conversation_uid',
        db_column='f_conversation_uid'
    )

    class Meta:
        db_table = 'image'  # Maps this model to the "image" table in the database

    def __str__(self):
        return f"Image<{self.image_uid}>"
