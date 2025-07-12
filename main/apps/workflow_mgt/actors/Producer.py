import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from main.utils.logger import log_trigger

class Producer:
    """
    Producer:
      - 將前端或後端的 HTTP 請求轉換為 WebSocket 訊息  
      - 透過 Django Channels 的 channel_layer 將訊息分發到對應 Topic  
    """

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def dispatch_topic(request):
        """
        流程:
          1) 檢查 payload (必填欄位 conversation_uid, text_content)
          2) 使用 channel_layer.group_send 將訊息推送給 Broker 
        """
        try:
            # (1) 檢查必填欄位
            payload = json.loads(request.body)
            required_fields = ["event_type", "conversation_uid", "text_content"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"Missing required fields: {', '.join(missing_fields)}"
                }, status=400)
            
            conversation_uid = payload["conversation_uid"]
            group_name = f"topic_{conversation_uid}"

            # (2) 使用 channel_layer.group_send 將訊息推送給 Broker 
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "broker_message", 
                    "payload": payload
                },
            )
			
            return JsonResponse({
                "status_code": 200,
                "message": "Dispatch successfully"
            }, status=200)

        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "message": str(e)
            }, status=500)
