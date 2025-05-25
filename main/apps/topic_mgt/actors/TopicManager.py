import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from main.utils.ApiKit import  json_request

class TopicManager:
    @csrf_exempt
    @require_http_methods(["POST"])
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

    # @csrf_exempt
    # @require_http_methods(["POST"])
    # def unsubscribe_topic(request):
    #     """
    #     POST /api/broker/<conversation_uid>/unsubscribe
    #     Body(JSON): { "group_name": "some_group" }
    #     將 group_name 從指定 conversation_uid 的訂閱清單中移除。
    #     """
    #     try:
    #         data = json.loads(request.body)
    #         group_name = data.get("group_name")
    #         if not group_name:
    #             return JsonResponse({"status": "error", "message": "Missing group_name"}, status=400)
            
    #         conversation_uid=data.get("conversation_uid")
    #         if not conversation_uid:
    #             return JsonResponse({"status": "error", "message": "Missing group_name"}, status=400)

    #         broker = TopicBroker()
    #         if not broker.topic_exists(conversation_uid):
    #             return JsonResponse({"status": "error", "message": "Topic does not exist"}, status=404)

    #         broker.unsubscribe(conversation_uid, group_name)
    #         return JsonResponse({
    #             "status": "ok",
    #             "message": f"Unsubscribed {group_name} from conversation {conversation_uid}"
    #         }, status=200)
    #     except Exception as e:
    #         return JsonResponse({"status": "error", "message": str(e)}, status=500)


    # @csrf_exempt
    # @require_http_methods(["POST"])
    # def get_subscribers(request):
    #     """
    #     GET /api/broker/<conversation_uid>/
    #     取得對應 conversation_uid 的所有訂閱者 group_name。
    #     """
    #     data = json.load(request.body)
    #     conversation_uid=data.get("conversation_uid")
    #     if not conversation_uid:
    #         return JsonResponse({"status": "error", "message": "Missing group_name"}, status=400)
        
    #     broker = TopicBroker()
    #     if not broker.topic_exists(conversation_uid):
    #         return JsonResponse({"status": "error", "message": "Topic does not exist"}, status=404)

    #     subscribers = broker.get_subscribers(conversation_uid)
    #     return JsonResponse({
    #         "status": "ok",
    #         "conversation_uid": conversation_uid,
    #         "subscribers": list(subscribers)
    #     }, status=200)


    # @csrf_exempt
    # @require_http_methods(["POST"])
    # def topic_exists(request):
    #     """
    #     GET /api/broker/<conversation_uid>/exists
    #     檢查 Redis 是否存在對應 conversation_uid 的 key。
    #     回傳 { "exists": True/False }
    #     """

    #     data = json.loads(request.body)
    #     conversation_uid=data.get("conversation_uid")
    #     if not conversation_uid:
    #         return JsonResponse({"status": "error", "message": "Missing group_name"}, status=400)

    #     broker = TopicBroker()
    #     exists = broker.topic_exists(conversation_uid)
    #     return JsonResponse({
    #         "status": "ok",
    #         "conversation_uid": conversation_uid,
    #         "exists": exists
    #     }, status=200)


    # @csrf_exempt
    # @require_http_methods(["POST"])
    # def broker_publish(request):
    #     """
    #     POST /api/broker/<conversation_uid>/publish
    #     Body(JSON): { "event_type": "some_event", "payload": { ... } }
    #     使用 Django Channels 的 group_send 廣播訊息給所有訂閱該 conversation_uid 的組。
    #     """
    #     try:
    #         data = json.loads(request.body)
    #         conversation_uid=data.get("conversation_uid")
    #         if not conversation_uid:
    #             return JsonResponse({"status": "error", "message": "Missing group_name"}, status=400)
    #         event_type = data.get("event_type")
    #         payload = data.get("payload", {})

    #         if not event_type:
    #             return JsonResponse({"status": "error", "message": "Missing event_type"}, status=400)

    #         broker = TopicBroker()
    #         if not broker.topic_exists(conversation_uid):
    #             return JsonResponse({"status": "error", "message": "Topic does not exist"}, status=404)

    #         # broker.publish 是 async function，因此要用 async_to_sync
    #         async_to_sync(broker.publish)(conversation_uid, event_type, payload)

    #         return JsonResponse({
    #             "status": "ok",
    #             "message": f"Published event '{event_type}' to conversation {conversation_uid}"
    #         }, status=200)
    #     except Exception as e:
    #         return JsonResponse({"status": "error", "message": str(e)}, status=500)
