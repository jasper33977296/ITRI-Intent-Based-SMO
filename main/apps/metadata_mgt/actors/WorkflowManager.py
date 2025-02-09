import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse

# 自訂的 logger decorator 與寫入工具 (請依您實際的 utils / logger 實作路徑)
from main.utils.logger import log_trigger, log_writer

# 您的 WorkflowController (請依實際路徑調整 import)
from main.apps.metadata_mgt.services.WorkflowController import WorkflowController

class WorkflowManager:
    """
    Manager 用來處理對外的 HTTP Request，並呼叫 WorkflowController 做實際資料存取與邏輯處理。
    """

    @csrf_exempt
    @log_trigger("INFO")
    @require_http_methods(["POST"])
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

            # 1) 驗證必填欄位
            if "conversation_uid" not in payload:
                return JsonResponse({
                    "status": False,
                    "message": "conversation_uid 為必填"
                }, status=400)

            # 2) 取出參數，若沒給則使用預設
            conversation_uid = payload["conversation_uid"]
            workflow_step = payload.get("workflow_step", "text_analysis")
            workflow_status = payload.get("workflow_status", "Running")

            # 3) 呼叫 Controller 建立
            result = WorkflowController.create_workflow(
                conversation_uid=conversation_uid,
                workflow_step=workflow_step,
                workflow_status=workflow_status,
            )
            return JsonResponse(result, status=result["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({"status": False, "message": "Invalid JSON"}, status=400)
        except Exception as e:
            # 記錄錯誤訊息到 logger
            log_writer(f"[create_workflow_metadata] Exception: {str(e)}", "ERROR")
            return JsonResponse({"status": False, "message": str(e)}, status=500)

    @csrf_exempt
    @log_trigger("INFO")
    @require_http_methods(["POST"])
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
            if "conversation_uid" not in payload:
                return JsonResponse({
                    "status": False,
                    "message": "conversation_uid 為必填"
                }, status=400)

            # 呼叫 Controller 查詢
            result = WorkflowController.get_workflow_by_conversation(payload["conversation_uid"])
            return JsonResponse(result, status=result["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({"status": False, "message": "Invalid JSON"}, status=400)
        except Exception as e:
            log_writer(f"[get_workflow_metadata] Exception: {str(e)}", "ERROR")
            return JsonResponse({"status": False, "message": str(e)}, status=500)

    @csrf_exempt
    @log_trigger("INFO")
    @require_http_methods(["POST"])
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
            if "conversation_uid" not in payload:
                return JsonResponse({
                    "status": False,
                    "message": "缺少conversation_uid"
                }, status=400)

            conversation_uid = payload.pop("conversation_uid")

            # 其餘欄位都視為可更新參數，丟到 Controller
            result = WorkflowController.update_workflow(conversation_uid, **payload)
            return JsonResponse(result, status=result["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({"status": False, "message": "Invalid JSON"}, status=400)
        except Exception as e:
            log_writer(f"[update_workflow_status] Exception: {str(e)}", "ERROR")
            return JsonResponse({"status": False, "message": str(e)}, status=500)

    @csrf_exempt
    @log_trigger("INFO")
    @require_http_methods(["POST"])
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
            if "conversation_uid" not in payload:
                return JsonResponse({
                    "status": False,
                    "message": "conversation_uid 為必填"
                }, status=400)

            result = WorkflowController.delete_workflow(payload["conversation_uid"])
            return JsonResponse(result, status=result["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({"status": False, "message": "Invalid JSON"}, status=400)
        except Exception as e:
            log_writer(f"[delete_workflow_metadata] Exception: {str(e)}", "ERROR")
            return JsonResponse({"status": False, "message": str(e)}, status=500)
