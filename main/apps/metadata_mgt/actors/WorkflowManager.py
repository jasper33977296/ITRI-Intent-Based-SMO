import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse

# 自訂的 logger decorator 與寫入工具 (請依您實際的 utils / logger 實作路徑)
from main.utils.logger import log_trigger

# 您的 WorkflowController (請依實際路徑調整 import)
from main.apps.metadata_mgt.services.WorkflowController import WorkflowController

class WorkflowManager:
    """
    Manager 用來處理對外的 HTTP Request，並呼叫 WorkflowController 做實際資料存取與邏輯處理。
    """

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def create_workflow_metadata(request):
        """
        建立對應的 Workflow metadata (一對一):
        必填: conversation_uid
        可選: workflow_step, workflow_status, start_time, end_time

        POST JSON:
        {
            "conversation_uid": "<uid>",            // 必填
            "workflow_step": "<string>",            // optional
            "workflow_status": "<string>",          // optional
        }
        """
        try:
            payload = json.loads(request.body)

            # 必填欄位檢查
            required_fields = ["conversation_uid"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"缺少必填欄位: {', '.join(missing_fields)}"
                }, status=400)
            
            # 2) 取出參數，若沒給則使用預設
            conversation_uid = payload["conversation_uid"]
            workflow_step = payload.get("workflow_step", "A")
            workflow_status = payload.get("workflow_status", "1")

            # 3) 呼叫 Controller 建立
            result = WorkflowController.create_workflow(
                conversation_uid=conversation_uid,
                workflow_step=workflow_step,
                workflow_status=workflow_status,
            )
            return JsonResponse(result, status=result["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({
                "status_code": 400,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "message": f"系統發生錯誤，請稍後再試: {str(e)}"
            }, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def get_workflow_metadata(request):
        """
        查詢該 Conversation 對應的唯一 Workflow:
        必填: conversation_uid

        POST JSON:
        {
            "conversation_uid": "<uid>"
        }
        """
        try:
            payload = json.loads(request.body)

            # 必填欄位檢查
            required_fields = ["conversation_uid"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"缺少必填欄位: {', '.join(missing_fields)}"
                }, status=400)

            # 呼叫 Controller 查詢
            result = WorkflowController.get_workflow_by_conversation(payload["conversation_uid"])
            
            return JsonResponse(result, status=result["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({
                "status_code": 400,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "message": f"系統發生錯誤，請稍後再試: {str(e)}"
            }, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def update_workflow_metadata(request):
        """
        修改對應 Conversation 的 Workflow:
        必填: conversation_uid
        可選: workflow_step, workflow_status, start_time, end_time

        POST JSON:
        {
            "conversation_uid": "<uid>",
            "workflow_step": "<string>",
            "workflow_status": "<string>",
            "start_time": "<string/datetime>",
            "end_time": "<string/datetime>"
        }
        """
        try:
            payload = json.loads(request.body)

            # 必填欄位檢查
            required_fields = ["conversation_uid"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"缺少必填欄位: {', '.join(missing_fields)}"
                }, status=400)

            conversation_uid = payload.pop("conversation_uid")

            # 其餘欄位都視為可更新參數，丟到 Controller
            result = WorkflowController.update_workflow(conversation_uid, **payload)

            return JsonResponse(result, status=result["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({
                "status_code": 400,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "message": f"系統發生錯誤，請稍後再試: {str(e)}"
            }, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def delete_workflow_metadata(request):
        """
        刪除該 Conversation 對應的 Workflow:
        必填: conversation_uid

        POST JSON:
        {
            "conversation_uid": "<uid>"
        }
        """
        try:
            payload = json.loads(request.body)

            # 必填欄位檢查
            required_fields = ["conversation_uid"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"缺少必填欄位: {', '.join(missing_fields)}"
                }, status=400)

            # 呼叫 Controller 刪除
            result = WorkflowController.delete_workflow(payload["conversation_uid"])

            return JsonResponse(result, status=result["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({
                "status_code": 400,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "message": f"系統發生錯誤，請稍後再試: {str(e)}"
            }, status=500)
