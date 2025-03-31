import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from main.apps.workflow_mgt.services.workflows import dify_single_intent_workflow
from main.utils.ApiKit import json_request

class WorkflowManager:
    """
    Workflow Manager:
      - 處理各種 decoupled tasks，如 analysis, scenario mapping, apiflow test & execute
      - 所有的對話都會經由 create_text decorator 紀錄 (由你自訂)
      - 不直接呼叫 Broker，若需通知前端 (WebSocket)，透過 Prosumer 提供的 API 進行
    """


    @csrf_exempt
    @require_http_methods(["POST"])
    def execute_workflow(request):
        """
        流程:
          1) 檢查 payload(必填欄位 conversation_uid, text)
          2) 呼叫 metadata_mgt API 取得該 conversation 的 workflow step & workflow status
          3) 根據 step 決定要呼叫的函式:
             text_analysis, require_scenario_mapping, scenario_apiflow_mapping,
             apiflow_orgainize, apiflow_test, apiflow_execute
          4) 透過 Prosumer 廣播給前端
        """
        try:
            # (1) 檢查必填欄位
            payload = json.loads(request.body)
            if "conversation_uid" not in payload:
                return JsonResponse({
                    "status": False,
                    "message": "Missing field: conversation_uid"
                }, status=400)
            conversation_uid = payload["conversation_uid"]

            text = payload.get("text")
        
            if not text:
                return JsonResponse({
                    "status": "error",
                    "message": "No text provided."
                }, status=400)

            if isinstance(text, dict):
                text_content = text.get("text_content", [])

            # (2) 呼叫 metadata_mgt 以取得 workflow step & status
            meta_payload = {"conversation_uid": conversation_uid}
            try:
                resp = json_request(
                    module="metadata_mgt",
                    actor="WorkflowManager",
                    function="get_workflow_metadata",
                    payload=meta_payload,
                )
                meta_data = resp.json()
            except Exception as e:
                return JsonResponse({
                    "status": "error",
                    "message": f"Fail to call metadata_mgt: {str(e)}"
                }, status=502)

            # 檢查後端回傳是否成功
            if not meta_data.get("status", False):
                return JsonResponse(meta_data, status=meta_data.get("status_code", 400))

            # 從回傳資料中取出 step, status
            workflow_info = meta_data.get("data", {})
            workflow_step = workflow_info.get("workflow_step", "demo")

            # (3) 根據 step 呼叫對應函式
            result = dify_single_intent_workflow(text_content)

            text_data = result.get("parsed_data","")

            return JsonResponse({
                    "event_type": workflow_step,
                    "conversation_uid": conversation_uid,
                    "text": text_data
            })

        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
        
    @csrf_exempt
    @require_http_methods(["POST"])
    def human_in_the_loop(request):
        """
        """
        
        