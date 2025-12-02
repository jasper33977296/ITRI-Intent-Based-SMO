import os
from django.core.exceptions import ObjectDoesNotExist
from main.apps.metadata_mgt.models.ConversationModel import Conversation
from main.apps.metadata_mgt.models.UserModel import User
from main.apps.metadata_mgt.models.AgentModel import Agent

class ConversationController:

    @staticmethod
    def create_conversation(f_user_uid, conversation_name="", f_agent_uid=None):
        """
        建立新的 Conversation (DB table: conversation)

        * conversation_path 路徑不由前端輸入，而是在此自動組合:
          格式: {CONVERSATION_FOLDER_PATH}/{user_uid}/{conversation_uid}.csv

        Input:
            user_uid: 使用者的 user_uid (UUID)
            conversation_name: (選填) 對話顯示名稱
            agent_uid: agent 的 agent_uid (UUID)

        Output:
            dict: {
               "status_code": <int>,
               "message": <str>,
               "data": {...} (若成功建立則回傳對應資料)
            }
        """
        try:
            # 1) 驗證使用者是否存在
            try:
                user = User.objects.get(user_uid=f_user_uid)
            except ObjectDoesNotExist:
                return {
                    "status_code": 404,
                    "message": f"找不到 user_uid = {f_user_uid}"
                }
            # 2) 驗證 agent 是否存在
            agent = None
            if f_agent_uid:
                try:
                    agent = Agent.objects.get(agent_uid=f_agent_uid)
                except ObjectDoesNotExist:
                    return {
                        "status_code": 404,
                        "message": f"找不到 agent_uid = {f_agent_uid}"
                    }
            # 3) 建立 Conversation 物件
            conversation = Conversation(
                f_user_uid=user,
                conversation_name=conversation_name,
                f_agent_uid=agent
            )
            conversation_path = f"""{os.environ.get("CONVERSATION_FOLDER_PATH")}/{f_user_uid}/{conversation.conversation_uid}.csv"""
            conversation.conversation_path = conversation_path
            conversation.save()

            return {
                "status_code": 201,
                "message": "成功創建對話",
                "data": {
                    "conversation_uid": str(conversation.conversation_uid),
                    "user_uid": str(conversation.f_user_uid.user_uid),
                    "agent_uid": str(conversation.f_agent_uid.agent_uid),
                    "conversation_path": conversation.conversation_path,  # 這裡是自動生成的路徑
                    "conversation_name": conversation.conversation_name,
                    "created_at": conversation.created_at.isoformat(),
                    "updated_at": conversation.updated_at.isoformat()
                }
            }
        except Exception as e:
            return {
                "status_code": 500,
                "message": f"系統發生錯誤: {str(e)}"
            }

    @staticmethod
    def get_conversation(conversation_uid):
        """
        取得單一 Conversation
        """
        try:
            conversation = Conversation.objects.get(conversation_uid=conversation_uid)
            return {
                "status_code": 200,
                "message": "成功取得對話",
                "data": {
                    "conversation_uid": str(conversation.conversation_uid),
                    "conversation_path": conversation.conversation_path,
                    "conversation_name": conversation.conversation_name,
                    "created_at": conversation.created_at.isoformat(),
                    "updated_at": conversation.updated_at.isoformat(),
                    "user_uid": str(conversation.f_user_uid.user_uid),
                }
            }
        except Conversation.DoesNotExist:
            return {
                "status_code": 404,
                "message": f"找不到 conversation_uid = {conversation_uid}"
            }
        except Exception as e:
            return {
                "status_code": 500,
                "message": f"系統發生錯誤: {str(e)}"
            }

    @staticmethod
    def get_user_conversation_metadata_list(user_uid, agent_uid=None):
        """
        取得指定 user_uid (可選 agent_uid) 的所有 conversation metadata

        * 當提供 agent_uid 時，必須同時符合 user_uid 與 agent_uid
        * 否則僅依據 user_uid 查詢

        Input:
            user_uid: 使用者的 user_uid (UUID)
            agent_uid: (選填) agent 的 agent_uid (UUID)

        Output:
            dict: {
               "status_code": <int>,
               "message": <str>,
               "data": [...](若成功取得則回傳對應資料列表)
            }
        """
        try:
            # 1) 驗證 user 是否存在
            try:
                user = User.objects.get(user_uid=user_uid)
            except ObjectDoesNotExist:
                return {
                    "status_code": 404,
                    "message": f"找不到 user_uid = {user_uid}"
                }
            # 2) 查詢 conversation
            if agent_uid:
                try:
                    agent = Agent.objects.get(agent_uid=agent_uid)
                except ObjectDoesNotExist:
                    return {
                        "status_code": 404,
                        "message": f"找不到 agent_uid = {agent_uid}"
                    }
                conversations = Conversation.objects.filter(f_user_uid=user, f_agent_uid=agent).order_by('-created_at')
            else:
                conversations = Conversation.objects.filter(f_user_uid=user).order_by('-created_at')
            data_list = []
            for c in conversations:
                data_list.append({
                    "conversation_uid": str(c.conversation_uid),
                    "conversation_path": c.conversation_path,
                    "conversation_name": c.conversation_name,
                    "created_at": c.created_at.isoformat(),
                    "updated_at": c.updated_at.isoformat(),
                    "user_uid": str(c.f_user_uid.user_uid),
                    "agent_uid": str(c.f_agent_uid.agent_uid)
                })

            return {
                "status_code": 200,
                "message": "成功取得使用者所有對話",
                "data": data_list
            }
        except Exception as e:
            return {
                "status_code": 500,
                "message": f"系統發生錯誤: {str(e)}"
            }

    @staticmethod
    def update_conversation_name(conversation_uid, conversation_name):
        """
        更新指定 Conversation 的名稱
        """
        try:
            conversation = Conversation.objects.get(conversation_uid=conversation_uid)
            conversation.conversation_name = conversation_name
            conversation.save()

            return {
                "status_code": 200,
                "message": "成功更新對話名稱"
            }
        except Conversation.DoesNotExist:
            return {
                "status_code": 404,
                "message": f"找不到 conversation_uid = {conversation_uid}"
            }
        except Exception as e:
            return {
                "status_code": 500,
                "message": f"系統發生錯誤: {str(e)}"
            }    

    @staticmethod
    def delete_conversation(conversation_uid):
        """
        刪除單一 Conversation
        """
        try:
            conversation = Conversation.objects.get(conversation_uid=conversation_uid)
            conversation.delete()
            return {
                "status_code": 200,
                "message": "成功刪除對話"
            }
        except Conversation.DoesNotExist:
            return {
                "status_code": 404,
                "message": f"找不到 conversation_uid = {conversation_uid}"
            }
        except Exception as e:
            return {
                "status_code": 500,
                "message": f"系統發生錯誤: {str(e)}"
            }
        
    @staticmethod
    def get_dify_conversation_id(conversation_uid):
        """
        取得指定 Conversation 的 Dify Conversation ID
        """
        try:
            conversation = Conversation.objects.get(conversation_uid=conversation_uid)
            return {
                "status_code": 200,
                "message": "成功取得 Dify conversation ID",
                "data": conversation.dify_conversation_id
            }
        except Conversation.DoesNotExist:
            return {
                "status_code": 404,
                "message": f"找不到 conversation_uid = {conversation_uid}"
            }
        except Exception as e:
            return {
                "status_code": 500,
                "message": f"系統發生錯誤: {str(e)}"
            }

    @staticmethod
    def update_dify_conversation_id(conversation_uid, dify_conversation_id):
        """
        更新指定 Conversation 的 Dify Conversation ID
        """
        try:
            conversation = Conversation.objects.get(conversation_uid=conversation_uid)
            conversation.dify_conversation_id = dify_conversation_id
            conversation.save()

            return {
                "status_code": 200,
                "message": "成功更新 Dify conversation ID"
            }
        except Conversation.DoesNotExist:
            return {
                "status_code": 404,
                "message": f"找不到 conversation_uid = {conversation_uid}"
            }
        except Exception as e:
            return {
                "status_code": 500,
                "message": f"系統發生錯誤: {str(e)}"
            }