from django.db import models
import uuid
from main.apps.metadata_mgt.models.UserModel import User
from main.apps.metadata_mgt.models.ConversationModel import Conversation

class Text(models.Model):
    text_id = models.AutoField(primary_key=True)  
    text_uid = models.UUIDField(default=uuid.uuid4, unique=True) 
    text_path = models.CharField(max_length=255) 
    created_at = models.DateTimeField(auto_now_add=True)


    f_conversation_uid  = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        to_field='conversation_uid',   
        db_column='f_conversation_uid'
    )

    # 對應到 User Model 的 user_uid 欄位 (外鍵)
    f_user_uid = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        to_field='user_uid',  
        db_column='f_user_uid'
    )

    class Meta:
        db_table = 'text'           # 指定對應的資料表名稱

    def __str__(self):
        return f"Text<{self.text_uid}>"