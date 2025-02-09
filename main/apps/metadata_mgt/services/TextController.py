# main/apps/metadata_mgt/services/text_controller.py
from django.core.exceptions import ObjectDoesNotExist
from main.apps.metadata_mgt.models.TextModel import Text
from main.apps.metadata_mgt.models.ConversationModel import Conversation
import uuid

class TextController:

    @staticmethod
    def create_text(conversation_uid):
        """
        建立一筆 Text 紀錄
        Input:
          - conversation_uid: Conversation 的 conversation_uid (UUID)
        Output:
          dict(status_code, status, message, data)
        """
        try:
            # 1) 驗證 Conversation 是否存在
            try:
                conversation = Conversation.objects.get(conversation_uid=conversation_uid)
            except ObjectDoesNotExist:
                return {
                    "status_code": 404,
                    "status": False,
                    "message": f"Conversation not found: {conversation_uid}"
                }

            # 2) 取得與該 Conversation 綁定的使用者
            user = conversation.f_user_uid  # 一定會有，不另做 User 檢查

            # 3) 設定 text_path 格式 texts/{conversation_uid}/{text_uid}.json
            #    這裡可以自行產生一個新的 text_uid (也可以讓 Model 用 default=uuid.uuid4 自動產生)
            new_text_uid = uuid.uuid4()
            text_path = f"texts/{conversation.conversation_uid}/{new_text_uid}.json"

            # 4) 建立 Text 資料
            text_obj = Text.objects.create(
                text_uid=new_text_uid,
                f_user_uid=user,
                f_conversation_uid=conversation,
                text_path=text_path
            )

            return {
                "status_code": 201,
                "status": True,
                "message": "Text created successfully",
                "data": {
                    "text_uid": str(text_obj.text_uid),
                    "user_uid": str(user.user_uid),
                    "conversation_uid": str(conversation.conversation_uid),
                    "text_path": text_obj.text_path,
                    "created_at": text_obj.created_at.isoformat()
                }
            }

        except Exception as e:
            return {
                "status_code": 500,
                "status": False,
                "message": f"Server error: {str(e)}"
            }

    @staticmethod
    def get_text_metadata_by_uid(text_uid):
        """
        依 text_uid 查詢單筆 Text
        """
        try:
            text_obj = Text.objects.get(text_uid=text_uid)
            return {
                "status_code": 200,
                "status": True,
                "message": "Get text success",
                "data": {
                    "text_uid": str(text_obj.text_uid),
                    "text_path": text_obj.text_path,
                    "created_at": text_obj.created_at.isoformat(),
                }
            }
        except Text.DoesNotExist:
            return {
                "status_code": 404,
                "status": False,
                "message": f"Text not found: {text_uid}"
            }
        except Exception as e:
            return {
                "status_code": 500,
                "status": False,
                "message": f"Server error: {str(e)}"
            }

    @staticmethod
    def get_text_list_by_conversation(conversation_uid):
        """
        依 conversation_uid 查詢所有 Text
        (例如: 取得該對話底下所有 text_uid 列表)
        """
        try:
            # 確認 conversation 存在
            if not Conversation.objects.filter(conversation_uid=conversation_uid).exists():
                return {
                    "status_code": 404,
                    "status": False,
                    "message": f"Conversation not found: {conversation_uid}"
                }
            
            texts = Text.objects.filter(f_conversation_uid__conversation_uid=conversation_uid).order_by('created_at')
            data_list = []
            for t in texts:
                data_list.append({
                    "text_uid": str(t.text_uid),
                    "text_path": t.text_path,
                    "created_at": t.created_at.isoformat(),
                    "f_user_uid": str(t.f_user_uid.user_uid)
                })
            
            return {
                "status_code": 200,
                "status": True,
                "message": f"Get texts success (count={len(data_list)})",
                "data": data_list
            }

        except Exception as e:
            return {
                "status_code": 500,
                "status": False,
                "message": f"Server error: {str(e)}"
            }

    @staticmethod
    def update_text(text_uid, **update_fields):
        """
        更新 text 紀錄 (根據 text_uid)
        update_fields 可包含 {"text_path": "..."} 等
        """
        try:
            text_obj = Text.objects.get(text_uid=text_uid)

            # 將 update_fields 裡可用的欄位更新到 text_obj
            allowed_fields = ["text_path"]
            for key, value in update_fields.items():
                if key in allowed_fields:
                    setattr(text_obj, key, value)

            text_obj.save()

            return {
                "status_code": 200,
                "status": True,
                "message": "Text updated successfully",
                "data": {
                    "text_uid": str(text_obj.text_uid),
                    "text_path": text_obj.text_path,
                    "created_at": text_obj.created_at.isoformat(),
                    "f_conversation_uid": str(text_obj.f_conversation_uid.conversation_uid),
                    "f_user_uid": str(text_obj.f_user_uid.user_uid)
                }
            }

        except Text.DoesNotExist:
            return {
                "status_code": 404,
                "status": False,
                "message": f"Text not found: {text_uid}"
            }
        except Exception as e:
            return {
                "status_code": 500,
                "status": False,
                "message": f"Server error: {str(e)}"
            }

    @staticmethod
    def delete_text_by_uid(text_uid):
        """
        刪除 text
        """
        try:
            text_obj = Text.objects.get(text_uid=text_uid)
            text_obj.delete()
            return {
                "status_code": 200,
                "status": True,
                "message": "Text deleted successfully"
            }
        except Text.DoesNotExist:
            return {
                "status_code": 404,
                "status": False,
                "message": f"Text not found: {text_uid}"
            }
        except Exception as e:
            return {
                "status_code": 500,
                "status": False,
                "message": f"Server error: {str(e)}"
            }
