import os
import json
import base64
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

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
            
            user_content = None

            if isinstance(text_content, list):
                user_content = text_content[0].get("content", "") 
            else:
                user_content = "" # 或自行定義預設行為 

            # (2) 呼叫 dify 執行工作流
            result = dify_single_intent_workflow(conversation_uid, user_content)
            if not result or "parsed_data" not in result:
                return JsonResponse({
                    "status_code": 502,
                    "message": "Failed execute workflow."
                }, status=502)
            text_data = result.get("parsed_data","")

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
    def human_in_the_loop(request):
        """
        流程:
          1) 檢查 payload(必填欄位 conversation_uid, text_content)
          2) 呼叫 workflow_mgt 以分發推播訊息
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
            
            # (2) 呼叫 workflow_mgt 以分發推播訊息
            meta_payload = {
                "conversation_uid": conversation_uid,
                "text_content": text_content,
            }
            try:
                resp = json_request(
                    module="workflow_mgt",
                    actor="Producer",
                    function="dispatch_topic",
                    payload=meta_payload,
                )
                meta_data = resp.json()
            except Exception as e:
                return JsonResponse({
                    "status_code": 502,
                    "message": f"Fail to call workflow_mgt API (dispatch_topic): {str(e)}"
                }, status=502)
            
            return JsonResponse({
                "status_code": 200,
                "message": "Success human in the loop."
            }, status=200)

        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "message": str(e)
            }, status=500)
    
    @csrf_exempt
    @require_http_methods(["POST"])
    def update_workflow_status(request):
        """
        流程:
        1) 檢查必填欄位
        2) 呼叫 metadata_mgt 以更新 workflow step & status
        """
        try:
            # (1) 檢查必填欄位
            payload = json.loads(request.body)
            required_fields = ["conversation_uid", "workflow_step", "workflow_status"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"Missing required fields: {', '.join(missing_fields)}"
                }, status=400)
			
            conversation_uid = payload["conversation_uid"]
            workflow_step = payload["workflow_step"]
            workflow_status = payload["workflow_status"]
            
            # (2) 呼叫 metadata_mgt 以更新 workflow step & status
            meta_payload = {
                "conversation_uid": conversation_uid,
                "workflow_step": workflow_step,
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

            # 檢查後端回傳是否成功 ==還需要更改==
            if not meta_data.get("status", False):
                return JsonResponse(meta_data, status=meta_data.get("status_code", 400))

            # 從回傳資料中取出 step, status
            workflow_info = meta_data.get("data", {})
            workflow_step = workflow_info.get("workflow_step", "demo")

            # (3) 根據 step 呼叫對應函式
            result = dify_single_intent_workflow(conversation_uid=conversation_uid,user_prompt=content)

            text_data = result.get("parsed_data","")

            return JsonResponse({
                    "event_type": workflow_step,
                    "conversation_uid": conversation_uid,
                    "text": text_data
            })

        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "message": str(e)
            }, status=500)
