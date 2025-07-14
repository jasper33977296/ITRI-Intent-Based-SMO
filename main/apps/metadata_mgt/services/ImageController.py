from django.core.exceptions import ObjectDoesNotExist
from main.apps.metadata_mgt.models.ImageModel import Image
from main.apps.metadata_mgt.models.ConversationModel import Conversation
import uuid

class ImageController:

    @staticmethod
    def create_image(conversation_uid):
        try:
            # 1) 驗證 Conversation 是否存在
            try:
                conversation = Conversation.objects.get(conversation_uid=conversation_uid)
            except ObjectDoesNotExist:
                return {
                    "status_code": 404,
                    "message": f"找不到 conversation_uid = {conversation_uid}"
                }

            # 2) 建立新 image_uid 與路徑
            new_image_uid = uuid.uuid4()
            image_path = f"images/{conversation_uid}/{new_image_uid}.png"

            # 3) 建立 Image 紀錄
            image_obj = Image.objects.create(
                image_uid=new_image_uid,
                image_path=image_path,
                f_conversation_uid=conversation
            )

            return {
                "status_code": 201,
                "message": "Image 建立成功",
                "data": {
                    "image_uid": str(image_obj.image_uid),
                    "conversation_uid": str(conversation.conversation_uid),
                    "image_path": image_obj.image_path,
                    "created_at": image_obj.created_at.isoformat()
                }
            }
        except Exception as e:
            return {
                "status_code": 500,
                "message": f"系統發生錯誤: {str(e)}"
            }

    @staticmethod
    def get_image_metadata_by_uid(image_uid):
        try:
            image = Image.objects.get(image_uid=image_uid)
            return {
                "status_code": 200,
                "message": "Image 查詢成功",
                "data": {
                    "image_uid": str(image.image_uid),
                    "conversation_uid": str(image.f_conversation_uid.conversation_uid),
                    "image_path": image.image_path,
                    "created_at": image.created_at.isoformat()
                }
            }
        except Image.DoesNotExist:
            return {
                "status_code": 404,
                "message": f"找不到 image_uid = {image_uid}"
            }
        except Exception as e:
            return {
                "status_code": 500,
                "message": f"系統發生錯誤: {str(e)}"
            }

    @staticmethod
    def get_image_list_by_conversation(conversation_uid):
        try:
            if not Conversation.objects.filter(conversation_uid=conversation_uid).exists():
                return {
                    "status_code": 404,
                    "message": f"找不到 conversation_uid = {conversation_uid}"
                }

            images = Image.objects.filter(f_conversation_uid=conversation_uid).order_by('created_at')
            data = [
                {
                    "image_uid": str(img.image_uid),
                    "image_path": img.image_path,
                    "created_at": img.created_at.isoformat()
                }
                for img in images
            ]

            return {
                "status_code": 200,
                "message": "Image 查詢清單成功",
                "data": data
            }
        except Exception as e:
            return {
                "status_code": 500,
                "message": f"系統發生錯誤: {str(e)}"
            }

    @staticmethod
    def delete_image_by_uid(image_uid):
        try:
            image = Image.objects.get(image_uid=image_uid)
            image.delete()
            return {
                "status_code": 200,
                "message": "Image 刪除成功"
            }
        except Image.DoesNotExist:
            return {
                "status_code": 404,
                "message": f"找不到 image_uid = {image_uid}"
            }
        except Exception as e:
            return {
                "status_code": 500,
                "message": f"系統發生錯誤: {str(e)}"
            }
