from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.exceptions import ValidationError
from main.apps.topic_mgt.services.broker import Broker as ServiceBroker
from django.http import JsonResponse
from main.utils.ApiKit import json_request
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from main.utils.TextDecorator import text_decorator
import json

class Broker(AsyncWebsocketConsumer):
    """
    角色：Topic broker
      - 管理 WS 連線 / 訂閱 / 斷線
      - 把 Producer 的訊息推送給同 Topic 的 Client 與 Consumer
      - 所有的對話都會經由 text_decorator 紀錄
    """
    @csrf_exempt
    @require_http_methods(["POST"])
    def create_topic(request):
        """
            1) 檢查必填欄位
            2) 呼叫 metadata_mgt 以確認 conversation 存在
            3) 註冊 topic
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
        
			# # (2) 呼叫 metadata_mgt 以確認 conversation 存在
            # try:
            #     resp = json_request(
            #         module="metadata_mgt",
            #         actor="ConversationManager",
            #         function="verify_conversation_exist",
            #         payload=payload,
            #     )
            #     meta_data = resp.json()
            # except Exception as e:
            #     return JsonResponse({
            #         "status_code": 502,
            #         "message": f"Fail to call metadata_mgt API (verify_conversation_exist): {str(e)}"
            #     }, status=502)
            
			# # ==還需要更改==
            # if not meta_data.get("status", False):
            #     return JsonResponse(meta_data, status=meta_data.get("status_code", 400))
            
			# (3) 註冊 topic
            broker = ServiceBroker()
            broker.init_topic(conversation_uid)
            return JsonResponse({
                "status_code": 201,
                "message": f"Initialized topic for conversation {conversation_uid}"
            }, status=201)
    
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "message": str(e)
            }, status=500)
        
    @csrf_exempt
    @require_http_methods(["POST"])
    def delete_topic(request):
        """
            1) 檢查必填欄位
            2) 刪除 topic
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
            
			# (2) 刪除 topic
            broker = ServiceBroker()
            broker.remove_topic(conversation_uid)
            return JsonResponse({
                "status_code": 200,
                "message": f"Removed topic for conversation {conversation_uid}"
            }, status=200)
        
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "message": str(e)
            }, status=500)

    async def connect(self):
        # 1) 取得 conversation_uid
        self.conversation_uid = self.scope["url_route"]["kwargs"].get("conversation_uid")
        self.group_name = f"topic_{self.conversation_uid}"

        # 2) 建立連線
        await self.accept()
        self.broker = ServiceBroker()

        # 3) 驗證 topic 是否已註冊
        exists = self.broker.topic_exists(self.conversation_uid)
        if not exists: 
            await self.close(code=4003, reason="conversation_uid not exist.")
            return
    
        # 4) 訂閱 topic
        self.broker.subscribe(self.conversation_uid, self.group_name)
        await self.channel_layer.group_add(self.group_name, self.channel_name)

    async def disconnect(self, code):
        # 1) 取消訂閱 topic
        self.broker.unsubscribe(self.conversation_uid, self.group_name)
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # -------- WebSocket 進來的資料（前端或其他 WS Client） --------
    @text_decorator(role="user")
    async def receive(self, text_data=None, bytes_data=None):
        try:
            payload = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({"error": "invalid json"}))
            return

        await self.channel_layer.send(
            "consumer",
            {"type": "send_message", "payload": payload},
        )

    # -------- 給 Producer 叫用：Broker.broker_message --------
    @text_decorator(role="llm")
    async def broker_message(self, event):
        """接收 Producer.dispatch_topic 轉來的訊息並推播給 WS Client"""
        await self.send(text_data=json.dumps(event["payload"]))
        # await self.send_json(payload=json.dumps(event["payload"]))

    # def _validate(self, event) -> None:
    #     """
    #     檢查 WS payload 是否符合:
    #     {
    #       "event_type": "text" | "demo",
    #       "conversation_uid": "<uuid string>",
    #       "text": <dict>
    #     }
    #     若不合法就 raise ValidationError
    #     """
    #     # 1) 檢查必填欄位
    #     required_fields = {"event_type", "conversation_uid", "text"}
    #     missing_fields = required_fields - event.keys()
    #     if missing_fields:
    #         raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

    #     # 2) event_type 合法值
    #     if event["event_type"] not in {"text", "demo"}:
    #         raise ValidationError("event_type must be 'text' or 'demo'.")

    #     # 3) text 物件
    #     text_obj = event["text"]
    #     if isinstance(text_obj, dict):
    #         raise ValidationError("text must be an object.")
            
    #     inner_required = {"role", "text_uid", "text_content"}
    #     missing_inner = inner_required - text_obj.keys()
    #     if missing_inner:
    #         raise ValidationError(f"text missing fields: {', '.join(missing_inner)}")

    #     # 4) text.text_content 物件
    #     text_array = text_obj["text_content"]
    #     if not isinstance(text_array, list):
    #         raise ValidationError("text.text_content must be a list.")
    #     if not text_array:                         # 若至少要有一筆
    #         raise ValidationError("text.text_content cannot be empty.")

    #     # 5) text.text_content.content 物件
    #     allowed_item_types = {"message", "image", "table"}
    #     for idx, item in enumerate(text_array):
    #         if not isinstance(item, dict):
    #             raise ValidationError(f"text.text_content[{idx}] must be an object.")
    #         if {"type", "content"} - item.keys():
    #             raise ValidationError(f"text.text_content[{idx}] missing 'type' or 'content'.")
    #         if item["type"] not in allowed_item_types:
    #             raise ValidationError(
    #                 f"text.text_content[{idx}].type must be one of {allowed_item_types}."
    #             )
