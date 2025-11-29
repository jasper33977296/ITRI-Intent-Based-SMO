from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import IntegrityError
from main.apps.metadata_mgt.models.AgentModel import Agent
from main.apps.metadata_mgt.models.UserModel import User
from main.apps.metadata_mgt.models.ConversationModel import Conversation


class AgentController:

    @staticmethod
    def create_agent(user_uid, agent_name, api_key):
        """
        創建新 agent。
        1. 驗證 user_uid 是否存在
        2. 創建 agent metadata
        """
        try:
            # 1) 驗證 user_uid 是否存在
            try:
                user = User.objects.get(user_uid=user_uid)
            except ObjectDoesNotExist:
                return {
                    "status_code": 404,
                    "message": "找不到對應的 user"
                }

            # 2) 驗證 api_key 是否可用（延遲匯入以避免循環）
            from main.apps.workflow_mgt.services.workflows import validate_dify_api_key
            verify = validate_dify_api_key(api_key)
            if verify.get("status_code") != 200:
                # 若是 API Key 無效（常見為 401），回傳更明確的提示；其他錯誤保留原訊息
                if verify.get("status_code") == 401:
                    return {
                        "status_code": 401,
                        "message": "無效的 Dify API Key，請確認後再試"
                    }
                return {
                    "status_code": verify.get("status_code", 500),
                    "message": verify.get('message', 'API key 驗證失敗')
                }

            # 3) 創建 agent
            agent = Agent(
                agent_name=agent_name,
                f_user_uid=user,
                api_key=api_key
            )
            agent.save()

            return {
                "status_code": 201,
                "message": "成功創建 agent",
                "data": {
                    "agent_uid": str(agent.agent_uid)
                }
            }

        except IntegrityError as e:
            return {
                "status_code": 400,
                "message": f"資料完整性錯誤: {str(e)}"
            }

        except ValidationError as e:
            return {
                "status_code": 400,
                "message": f"驗證失敗: {str(e)}"
            }

        except Exception as e:
            return {
                "status_code": 500,
                "message": f"伺服器內部錯誤: {str(e)}"
            }

    @staticmethod
    def get_agent_name(agent_uid):
        """
        取得單一 agent 名稱。
        """
        try:
            agent = Agent.objects.get(agent_uid=agent_uid)

            return {
                "status_code": 200,
                "message": "成功取得單一 agent 名稱",
                "data": {
                    "agent_uid": str(agent.agent_uid),
                    "agent_name": agent.agent_name
                }
            }

        except ObjectDoesNotExist:
            return {
                "status_code": 404,
                "message": "找不到對應的 agent"
            }

        except Exception as e:
            return {
                "status_code": 500,
                "message": f"伺服器內部錯誤: {str(e)}"
            }

    @staticmethod
    def get_agent(agent_uid):
        """
        取得單一 agent 詳細資料 (包含 user_uid)。
        """
        try:
            agent = Agent.objects.get(agent_uid=agent_uid)
            return {
                "status_code": 200,
                "message": "成功取得 agent 詳細資料",
                "data": {
                    "agent_uid": str(agent.agent_uid),
                    "agent_name": agent.agent_name,
                    "api_key": agent.api_key,
                    "user_uid": str(agent.f_user_uid.user_uid)
                }
            }
        except ObjectDoesNotExist:
            return {
                "status_code": 404,
                "message": "找不到對應的 agent"
            }
        except Exception as e:
            return {
                "status_code": 500,
                "message": f"伺服器內部錯誤: {str(e)}"
            }

    @staticmethod
    def get_agent_list(user_uid):
        """
        取得使用者的 agent 清單。
        """
        try:
            # 1) 驗證 user_uid 是否存在
            try:
                user = User.objects.get(user_uid=user_uid)
            except ObjectDoesNotExist:
                return {
                    "status_code": 404,
                    "message": "找不到對應的 user"
                }

            # 2) 查詢該使用者的所有 agent
            agents = Agent.objects.filter(f_user_uid=user)

            agent_list = [
                {
                    "agent_uid": str(agent.agent_uid),
                    "agent_name": agent.agent_name
                }
                for agent in agents
            ]

            return {
                "status_code": 200,
                "message": "成功取得使用者的 agent",
                "data": agent_list
            }

        except Exception as e:
            return {
                "status_code": 500,
                "message": f"伺服器內部錯誤: {str(e)}"
            }

    @staticmethod
    def update_agent(agent_uid, agent_name=None, api_key=None):
        """
        更新 agent metadata。
        """
        try:
            # 1) 查詢 agent
            try:
                agent = Agent.objects.get(agent_uid=agent_uid)
            except ObjectDoesNotExist:
                return {
                    "status_code": 404,
                    "message": "找不到對應的 agent"
                }

            # 2) 更新欄位
            if agent_name is not None:
                agent.agent_name = agent_name
            if api_key is not None:
                # 驗證 api_key 有效性（延遲匯入以避免循環）
                from main.apps.workflow_mgt.services.workflows import validate_dify_api_key
                verify = validate_dify_api_key(api_key)
                if verify.get("status_code") != 200:
                    return {
                        "status_code": 401,
                        "message": "無效的 Dify API Key，請確認後再試"
                    }
                agent.api_key = api_key

            agent.save()

            return {
                "status_code": 200,
                "message": "成功更新 agent"
            }

        except ValidationError as e:
            return {
                "status_code": 400,
                "message": f"驗證失敗: {str(e)}"
            }

        except Exception as e:
            return {
                "status_code": 500,
                "message": f"伺服器內部錯誤: {str(e)}"
            }

    @staticmethod
    def delete_agent(agent_uid):
        """
        刪除 agent metadata。
        """
        try:
            # 1) 查詢 agent
            try:
                agent = Agent.objects.get(agent_uid=agent_uid)
            except ObjectDoesNotExist:
                return {
                    "status_code": 404,
                    "message": "找不到對應的 agent"
                }

            # 2) 檢查該 user 剩餘 agent 數量，若只剩一個則阻擋刪除
            user = agent.f_user_uid
            remaining_count = Agent.objects.filter(f_user_uid=user).count()
            if remaining_count <= 1:
                return {
                    "status_code": 400,
                    "message": "用戶至少需存在一個 Agent"
                }

            # 3) 刪除 agent
            agent.delete()

            return {
                "status_code": 200,
                "message": "成功刪除 agent"
            }

        except Exception as e:
            return {
                "status_code": 500,
                "message": f"伺服器內部錯誤: {str(e)}"
            }

    @staticmethod
    def get_agent_api_key_by_conversation(conversation_uid):
        """
        透過 conversation_uid 取得對應的 agent api_key。
        """
        try:
            
            # 1) 查詢 conversation
            try:
                conversation = Conversation.objects.get(conversation_uid=conversation_uid)
            except ObjectDoesNotExist:
                return {
                    "status_code": 404,
                    "message": "找不到對應的 conversation"
                }

            # 2) 取得 agent
            agent = conversation.f_agent_uid
            if not agent:
                return {
                    "status_code": 404,
                    "message": "conversation 沒有關聯的 agent"
                }

            # 3) 回傳 api_key
            return {
                "status_code": 200,
                "message": "成功取得 agent api_key",
                "data": {
                    "api_key": str(agent.api_key)
                }
            }

        except Exception as e:
            return {
                "status_code": 500,
                "message": f"伺服器內部錯誤: {str(e)}"
            }
