from django.db import models
import uuid
from main.apps.metadata_mgt.models.ConversationModel import Conversation

class Image(models.Model):
    image_id = models.AutoField(primary_key=True)  
    image_uid = models.UUIDField(default=uuid.uuid4, unique=True) 
    image_path = models.CharField(max_length=255) 
    created_at = models.DateTimeField(auto_now_add=True)


    f_conversation_uid  = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        to_field='conversation_uid',   
        db_column='f_conversation_uid'
    )

    class Meta:
        db_table = 'image'           # 指定對應的資料表名稱

    def __str__(self):
        return f"Image<{self.image_uid}>"