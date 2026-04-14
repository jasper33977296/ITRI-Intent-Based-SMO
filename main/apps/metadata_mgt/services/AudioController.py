from django.core.exceptions import ObjectDoesNotExist
from main.apps.metadata_mgt.models.AudioModel import Audio
from main.apps.metadata_mgt.models.ConversationModel import Conversation
import uuid

class AudioController:

    @staticmethod
    def create_audio(conversation_uid):
        try:
            try:
                conversation = Conversation.objects.get(conversation_uid=conversation_uid)
            except ObjectDoesNotExist:
                return {
                    "status_code": 404,
                    "message": f"找不到 conversation_uid = {conversation_uid}"
                }

            new_audio_uid = uuid.uuid4()
            audio_path = f"audios/{conversation_uid}/{new_audio_uid}.webm"

            audio_obj = Audio.objects.create(
                audio_uid=new_audio_uid,
                audio_path=audio_path,
                f_conversation_uid=conversation
            )

            return {
                "status_code": 201,
                "message": "Audio 建立成功",
                "data": {
                    "audio_uid": str(audio_obj.audio_uid),
                    "conversation_uid": str(conversation.conversation_uid),
                    "audio_path": audio_obj.audio_path,
                    "created_at": audio_obj.created_at.isoformat()
                }
            }
        except Exception as e:
            return {
                "status_code": 500,
                "message": f"系統發生錯誤: {str(e)}"
            }

    @staticmethod
    def get_audio_metadata_by_uid(audio_uid):
        try:
            audio = Audio.objects.get(audio_uid=audio_uid)
            return {
                "status_code": 200,
                "message": "Audio 查詢成功",
                "data": {
                    "audio_uid": str(audio.audio_uid),
                    "conversation_uid": str(audio.f_conversation_uid.conversation_uid),
                    "audio_path": audio.audio_path,
                    "created_at": audio.created_at.isoformat()
                }
            }
        except Audio.DoesNotExist:
            return {
                "status_code": 404,
                "message": f"找不到 audio_uid = {audio_uid}"
            }
        except Exception as e:
            return {
                "status_code": 500,
                "message": f"系統發生錯誤: {str(e)}"
            }

    @staticmethod
    def get_audio_list_by_conversation(conversation_uid):
        try:
            if not Conversation.objects.filter(conversation_uid=conversation_uid).exists():
                return {
                    "status_code": 404,
                    "message": f"找不到 conversation_uid = {conversation_uid}"
                }

            audios = Audio.objects.filter(f_conversation_uid=conversation_uid).order_by('created_at')
            data = [
                {
                    "audio_uid": str(a.audio_uid),
                    "audio_path": a.audio_path,
                    "created_at": a.created_at.isoformat()
                }
                for a in audios
            ]

            return {
                "status_code": 200,
                "message": "Audio 查詢清單成功",
                "data": data
            }
        except Exception as e:
            return {
                "status_code": 500,
                "message": f"系統發生錯誤: {str(e)}"
            }

    @staticmethod
    def delete_audio_by_uid(audio_uid):
        try:
            audio = Audio.objects.get(audio_uid=audio_uid)
            audio.delete()
            return {
                "status_code": 200,
                "message": "Audio 刪除成功"
            }
        except Audio.DoesNotExist:
            return {
                "status_code": 404,
                "message": f"找不到 audio_uid = {audio_uid}"
            }
        except Exception as e:
            return {
                "status_code": 500,
                "message": f"系統發生錯誤: {str(e)}"
            }
