from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import IntegrityError
from main.apps.metadata_mgt.models.WorkflowModel import Workflow
from main.apps.metadata_mgt.models.ConversationModel import Conversation
from datetime import datetime

class WorkflowController:
    @staticmethod
    def create_workflow(conversation_uid, workflow_step, workflow_status, start_time=None, end_time=None):
        """
        建立新的 Workflow (一對一)：
          1. 確認指定的 Conversation 存在
          2. 確認該 Conversation 尚無 Workflow (可不做程式檢查，但若已有 Workflow 會觸發 IntegrityError)
          3. 建立並儲存 Workflow
        """
        try:
            # 1) 找到對應的 Conversation
            conversation_obj = Conversation.objects.get(conversation_uid=conversation_uid)

            # 2) 可選擇事先檢查該 Conversation 是否已綁定 Workflow
            #    若您想在程式中顯式攔截，可以用下列檢查：
            if hasattr(conversation_obj, 'workflow'):
                return {
                    "status_code": 400,
                    "status": False,
                    "message": "該 Conversation 已有 Workflow，不可重複建立 (一對一限制)"
                }

            # 3) 建立新的 Workflow
            workflow = Workflow(
                f_conversation_uid=conversation_obj,
                workflow_step=workflow_step,
                workflow_status=workflow_status,
                start_time=datetime.now(),
                end_time=datetime.now()
            )
            workflow.save()

            return {
                "status_code": 201,
                "status": True,
                "message": "Workflow 建立成功",
                "data": {
                    "workflow_id": workflow.workflow_id
                }
            }

        except Conversation.DoesNotExist:
            return {
                "status_code": 404,
                "status": False,
                "message": "指定的 Conversation 不存在，無法建立 Workflow"
            }
        except IntegrityError as e:
            # 若 DB 已存在該 conversation_uid 的 workflow，unique constraint 會報錯
            return {
                "status_code": 400,
                "status": False,
                "message": f"建立失敗，該 Conversation 已綁定 Workflow 或其他資料庫錯誤: {str(e)}"
            }
        except ValidationError as e:
            return {
                "status_code": 400,
                "status": False,
                "message": f"驗證失敗: {e.message_dict}"
            }
        except Exception as e:
            return {
                "status_code": 500,
                "status": False,
                "message": f"伺服器內部錯誤: {str(e)}"
            }

    @staticmethod
    def get_workflow_by_conversation(conversation_uid):
        """
        以 conversation_uid 查詢對應的唯一 Workflow (一對一)。
        回傳該 Workflow 的所有欄位資訊。
        """
        try:
            conversation_obj = Conversation.objects.get(conversation_uid=conversation_uid)
            # 因為一對一可直接 conversation_obj.workflow 或透過 filter/get
            workflow = Workflow.objects.get(f_conversation_uid=conversation_obj)

            return {
                "status_code": 200,
                "status": True,
                "message": "查詢 Workflow 成功",
                "data": {
                    "workflow_id": workflow.workflow_id,
                    "workflow_step": workflow.workflow_step,
                    "workflow_status": workflow.workflow_status,
                    "start_time": workflow.start_time,
                    "end_time": workflow.end_time
                }
            }

        except Conversation.DoesNotExist:
            return {
                "status_code": 404,
                "status": False,
                "message": "指定的 Conversation 不存在"
            }
        except Workflow.DoesNotExist:
            return {
                "status_code": 404,
                "status": False,
                "message": "尚未為該 Conversation 建立 Workflow"
            }
        except Exception as e:
            return {
                "status_code": 500,
                "status": False,
                "message": f"伺服器內部錯誤: {str(e)}"
            }

    @staticmethod
    def update_workflow(conversation_uid, **kwargs):
        """
        以 conversation_uid 更新該 Conversation 下的唯一 Workflow。
        可更新欄位: workflow_step, workflow_status, start_time, end_time
        """
        try:
            conversation_obj = Conversation.objects.get(conversation_uid=conversation_uid)
            workflow = Workflow.objects.get(f_conversation_uid=conversation_obj)

            # 遍歷要更新的欄位
            for key, value in kwargs.items():
                if hasattr(workflow, key):
                    setattr(workflow, key, value)

            workflow.save()
            return {
                "status_code": 200,
                "status": True,
                "message": "Workflow 更新成功"
            }

        except Conversation.DoesNotExist:
            return {
                "status_code": 404,
                "status": False,
                "message": "指定的 Conversation 不存在"
            }
        except Workflow.DoesNotExist:
            return {
                "status_code": 404,
                "status": False,
                "message": "尚未為該 Conversation 建立 Workflow"
            }
        except IntegrityError as e:
            return {
                "status_code": 400,
                "status": False,
                "message": f"更新失敗: {str(e)}"
            }
        except ValidationError as e:
            return {
                "status_code": 400,
                "status": False,
                "message": f"驗證失敗: {e.message_dict}"
            }
        except Exception as e:
            return {
                "status_code": 500,
                "status": False,
                "message": f"伺服器內部錯誤: {str(e)}"
            }

    @staticmethod
    def delete_workflow(conversation_uid):
        """
        刪除該 conversation_uid 下唯一的 Workflow (一對一)。
        """
        try:
            conversation_obj = Conversation.objects.get(conversation_uid=conversation_uid)
            workflow = Workflow.objects.get(f_conversation_uid=conversation_obj)

            workflow.delete()
            return {
                "status_code": 200,
                "status": True,
                "message": f"Workflow 已刪除 (conversation_uid={conversation_uid})"
            }

        except Conversation.DoesNotExist:
            return {
                "status_code": 404,
                "status": False,
                "message": "指定的 Conversation 不存在"
            }
        except Workflow.DoesNotExist:
            return {
                "status_code": 404,
                "status": False,
                "message": "尚未為該 Conversation 建立 Workflow"
            }
        except Exception as e:
            return {
                "status_code": 500,
                "status": False,
                "message": f"伺服器內部錯誤: {str(e)}"
            }
