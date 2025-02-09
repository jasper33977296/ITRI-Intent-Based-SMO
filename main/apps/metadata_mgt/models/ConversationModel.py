from django.db import models
import uuid
from main.apps.metadata_mgt.models.UserModel import User

class Conversation(models.Model):
    conversation_id = models.AutoField(primary_key=True) 
    conversation_uid = models.UUIDField(default=uuid.uuid4, unique=True) 
    conversation_path = models.CharField(max_length=255)
    conversation_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  

    # f_user_uid 為外鍵，對應到 User Model 的 user_uid 欄位
    f_user_uid = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        to_field='user_uid',  # 指定要關聯到 User Model 中的 user_uid 欄位
        db_column='f_user_uid'  # 指定在本 Model 所對應的資料庫欄位名稱
    )

    class Meta:
        db_table = 'conversation'

    def __str__(self):
        return str(self.conversation_uid)