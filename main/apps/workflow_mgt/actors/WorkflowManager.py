import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from main.utils.logger import log_trigger, log_writer

from main.apps.workflow_mgt.services.workflows import dify_single_intent_workflow
from main.utils.ApiKit import json_request

class WorkflowManager:
    """
    Workflow Manager:
      - 處理各種 decoupled tasks，如 analysis, scenario mapping, apiflow test & execute
      - 不直接呼叫 Broker，若需通知前端 (WebSocket)，透過 Producer 提供的 API 進行
    """

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def execute_workflow(request):
        """
        流程:
          1) 檢查 payload(必填欄位 conversation_uid, text_content)
          2) 呼叫 呼叫 dify 執行工作流
        """
        try:
            # (1) 檢查必填欄位
            payload = json.loads(request.body)
            required_fields = ["conversation_uid", "text_content"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"Missing required fields: {', '.join(missing_fields)}"
                }, status=400)
			
            conversation_uid = payload["conversation_uid"]
            text_content = payload["text_content"]

            user_content = ""
            image_items = []
            audio_items = []

            if isinstance(text_content, list):
                text_items = [t for t in text_content if t.get("type") == "message"]
                image_items = [t for t in text_content if t.get("type") == "image"]
                audio_items = [t for t in text_content if t.get("type") == "audio"]
                user_content = text_items[0].get("content", "") if text_items else ""
                
            # 更新 workflow status 1
            work_payload = {
                "conversation_uid": conversation_uid,
                "workflow_status": "1"
            }

            try:
                resp = json_request(
                    module="workflow_mgt",
                    actor="WorkflowManager",
                    function="update_workflow_status",
                    payload=work_payload,
                )
                work_data = resp.json()
            except Exception as e:
                print("Workflow 更新失敗: ", e)

            # 檢查後端回傳是否成功
            if not work_data.get("status_code", 400):
                return JsonResponse(work_data, status_code=work_data.get("status_code", 400))

            # (2) 呼叫 dify 執行工作流
            result = dify_single_intent_workflow(conversation_uid, user_content, image_items, audio_items)
            if not result or "data" not in result:
                return JsonResponse({
                    "status_code": 502,
                    "message": "Failed execute workflow."
                }, status=502)
            text_data = result.get("data","")

            return JsonResponse({
                "status_code": 200,
                "message": "Success execute workflow"
            })

        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "message": str(e)
            }, status=500)
    
    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def update_workflow_status(request):
        """
        流程:
        1) 檢查必填欄位
        2) 呼叫 metadata_mgt 以更新 workflow step & status
        """
        try:
            # (1) 檢查必填欄位
            payload = json.loads(request.body)
            required_fields = ["conversation_uid", "workflow_status"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"Missing required fields: {', '.join(missing_fields)}"
                }, status=400)
			
            conversation_uid = payload["conversation_uid"]
            workflow_status = payload["workflow_status"]
            
            # (2) 呼叫 metadata_mgt 以更新 workflow step & status
            meta_payload = {
                "conversation_uid": conversation_uid,
                "workflow_step": payload.get("workflow_step"),
                "workflow_status": workflow_status,
                "start_time": payload.get("start_time"),
                "end_time": payload.get("end_time"),
            }

            meta_payload = {k: v for k, v in meta_payload.items() if v is not None}
            try:
                resp = json_request(
                    module="metadata_mgt",
                    actor="WorkflowManager",
                    function="update_workflow_metadata",
                    payload=meta_payload,
                )
                meta_data = resp.json()
            except Exception as e:
                return JsonResponse({
                    "status_code": 502,
                    "message": f"Fail to call metadata_mgt API (get_workflow_metadata): {str(e)}"
                }, status=502)

            # 檢查後端回傳是否成功
            if not meta_data.get("status_code", 400):
                return JsonResponse(meta_data, status_code=meta_data.get("status_code", 400))

            return JsonResponse({
                "status_code": 200,
                "message": "Workflow 更新成功"
            })

        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "message": str(e)
            }, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def logger_human_in_the_loop(request):
        """
        流程:
          1) 檢查 payload (必填欄位 conversation_uid, text_uid, text_content)
          2) 呼叫 metadata_mgt API 取得該 conversation 的 workflow step & workflow status
          3) 根據 workflow status 處理:
             - 若 status="start": 創建一個新的 text
             - 若 status="running": 加入訊息到該 text
             - 若 status="finish": 更新 workflow status 為 finish (或其他收尾處理)
          4) 透過 Prosumer 廣播給前端
        """
        try:
            payload = json.loads(request.body)

            # 必填欄位檢查
            required_fields = ["status_code","message"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"缺少必填欄位: {', '.join(missing_fields)}"
                }, status=400)

            log_writer(
                log_level="ERROR",
                status_code=payload["status_code"],
                source_type="dify engine",
                func="workflow_mgt/ WorkflowManager/ logger_human_in_the_loop",
                args=[payload],
                message=payload["message"]
            )

            # 最後回傳 HTTP 結果
            return JsonResponse({
                "status_code": 200,
                "message": "Logger Human in the loop processed successfully",
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"status_code": 400, "message": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"status_code": 500, "message": str(e)}, status=500)