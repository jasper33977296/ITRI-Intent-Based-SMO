import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from main.apps.workflow_mgt.services.workflows import text_analysis
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
            
            user_content = None

            if isinstance(text, dict):
                text_content = text.get("text_content", [])
                if text_content and isinstance(text_content, list):
                    user_content = text_content[0].get("content", "") 
                else:
                    user_content = ""  # 或自行定義預設行為

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
            workflow_step = workflow_info.get("workflow_step", "text_analysis")

            # (3) 根據 step 呼叫對應函式
            if workflow_step == "text_analysis":
                result = text_analysis(user_content)
            # elif workflow_step == "require_scenario_mapping":
            #     result = require_scenario_mapping(user_content)
            #     event_type = "require_scenario_mapping"
            # elif workflow_step == "scenario_apiflow_mapping":
            #     result = scenario_apiflow_mapping(user_content)
            #     event_type = "scenario_apiflow_mapping"
            # elif workflow_step == "apiflow_orgainize":
            #     result = apiflow_orgainize(user_content)
            #     event_type = "apiflow_orgainize"
            # elif workflow_step == "apiflow_test":
            #     result = apiflow_test(user_content)
            #     event_type = "apiflow_test"
            # elif workflow_step == "apiflow_execute":
            #     result = apiflow_execute(user_content)
            #     event_type = "apiflow_execute"
            else:
                # 若不在預期清單內，就當作未知
                result = f"Unknown workflow_step ({workflow_step}). content={user_content}"

            return JsonResponse({
                    "event_type": workflow_step,
                    "conversation_uid": conversation_uid,
                    "text": result
            })

        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
        

    def require_scenario_mapping(request):
        """
        對 conversation 進行情境對應 (scenario mapping)
        Input JSON: {
            "conversation_uid": "..."
        }
        """
        conversation_uid = request.POST.get("conversation_uid")
        if not conversation_uid:
            return JsonResponse({"status":"error","message":"No conversation_uid provided."}, status=400)

        # 假設做一些情境對應的邏輯
        # scenario_result = do_scenario_mapping(...)

        # broadcast_to_prosumer(conversation_uid, "scenario_mapping", {"result": scenario_result})
        return JsonResponse({"status":"ok","message":"Scenario mapping requested."})

    def scenario_apiflow_mapping(request):
        """
        對 conversation 進行 API Flow 情境對應
        Input JSON: {
            "conversation_uid": "..."
        }
        """
        conversation_uid = request.POST.get("conversation_uid")
        if not conversation_uid:
            return JsonResponse({"status":"error","message":"No conversation_uid provided."}, status=400)

        # do_something...
        # broadcast_to_prosumer(conversation_uid, "apiflow_mapping", {...})

        return JsonResponse({"status":"ok","message":"Scenario APIFlow mapping requested."})


    def apiflow_test(request):
        """
        測試指定 conversation 的 API Flow
        Input JSON:
        {
            "conversation_uid": "...",
            "test_params": {...}
        }
        """
        conversation_uid = request.POST.get("conversation_uid")
        test_params = request.POST.get("test_params", {})

        if not conversation_uid:
            return JsonResponse({"status":"error","message":"No conversation_uid provided."}, status=400)

        # do_apiflow_test...
        # broadcast_to_prosumer(conversation_uid, "apiflow_test", {...})

        return JsonResponse({"status":"ok","message":"APIFlow test requested."})


    def apiflow_execute(request):
        """
        執行指定 conversation 的 API Flow
        Input JSON:
        {
            "conversation_uid": "...",
            "execute_params": {...}
        }
        """
        conversation_uid = request.POST.get("conversation_uid")
        execute_params = request.POST.get("execute_params", {})

        if not conversation_uid:
            return JsonResponse({"status":"error","message":"No conversation_uid provided."}, status=400)

        # do_apiflow_execute...
        # broadcast_to_prosumer(conversation_uid, "apiflow_execute", {...})

        return JsonResponse({"status":"ok","message":"APIFlow execute requested."})