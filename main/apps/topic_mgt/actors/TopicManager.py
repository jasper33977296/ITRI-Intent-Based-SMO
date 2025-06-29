import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from main.utils.ApiKit import  json_request
from main.utils.logger import log_trigger

class TopicManager:
    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def create_topic(request):
        """
            1) 檢查必填欄位  
            2) 呼叫 topic_mgt 建立 topic  
        """
        try:
            # (1) 檢查必填欄位
            payload = json.loads(request.body)
            required_fields = ["conversation_uid"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"Missing required fields: {', '.join(missing_fields)}"
                }, status=400)
                
            conversation_uid = payload["conversation_uid"]

            # (2) 呼叫 topic_mgt 以創建 topic
            try:
                topic_payload = {"conversation_uid": conversation_uid}
                resp = json_request(
                    module="topic_mgt",
                    actor="Broker",
                    function="create_topic",
                    payload=topic_payload,
                )
            except Exception as e:
                return JsonResponse({
                    "status_code": 502,
                    "message": f"Fail to call topic_mgt API (create_topic): {str(e)}"
                }, status=502)
            
            return JsonResponse({
                "status_code": 201,
                "message": "Topic created successfully"
            }, status=201)
        
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "message": str(e)
            }, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def delete_topic(request):
        """
            1) 檢查必填欄位  
            2) 呼叫 topic_mgt 刪除 topic  
        """
        try:
            # (1) 檢查必填欄位
            payload = json.loads(request.body)
            required_fields = ["conversation_uid"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"Missing required fields: {', '.join(missing_fields)}"
                }, status=400)
                
            conversation_uid = payload["conversation_uid"]

            # (2) 呼叫 topic_mgt 以刪除 topic
            try:
                topic_payload = {"conversation_uid": conversation_uid}
                resp = json_request(
                    module="topic_mgt",
                    actor="Broker",
                    function="delete_topic",
                    payload=topic_payload,
                )
            except Exception as e:
                return JsonResponse({
                    "status_code": 502,
                    "message": f"Fail to call topic_mgt API (delete_topic): {str(e)}"
                }, status=502)
            
            return JsonResponse({
                "status_code": 200,
                "message": "Topic deleted successfully"
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "message": str(e)
            }, status=500)
