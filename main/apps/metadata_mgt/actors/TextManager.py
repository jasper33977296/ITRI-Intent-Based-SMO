from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json

from main.apps.metadata_mgt.services.TextController import TextController

class TextManager:
    @csrf_exempt
    @require_http_methods(["POST"])
    def create_text_metadata(request):
        try:
            payload = json.loads(request.body)

            required_fields = ["conversation_uid"]
            missing = [f for f in required_fields if f not in payload]
            if missing:
                return JsonResponse({
                    "status_code": 400,
                    "status": False,
                    "message": f"Missing field(s): {', '.join(missing)}"
                }, status=400)

            response = TextController.create_text(
                conversation_uid=payload["conversation_uid"],
            )
            return JsonResponse(response, status=response["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({
                "status_code": 400,
                "status": False,
                "message": "Invalid JSON"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "status": False,
                "message": str(e)
            }, status=500)
        
    @csrf_exempt
    @require_http_methods(["POST"])
    def get_text_metadata(request):
        """
        Input (POST JSON):
        {
            "text_uid": <string>
        }

        Output (JsonResponse):
        {
            "status": <bool>,
            "message": <string>,
            "data": {
                "text_uid": <string>,
                "text_path": <string>,
                "created_at": <string>
            }
        }
        """
        try:
            payload = json.loads(request.body)

            # (1) 檢查必填欄位
            if "text_uid" not in payload:
                return JsonResponse({
                    "status": False,
                    "message": "缺少必填欄位: text_uid"
                }, status=400)

            # (2) 透過 text_uid 找對應的 text metadata
            response = TextController.get_text_metadata_by_uid(payload["text_uid"])

            # 整理回傳給前端的 JSON
            return JsonResponse({
                "status": response["status"],
                "message": response["message"],
                "data": response.get("data", {})
            }, status=response["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({
                "status": False,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"系統發生錯誤，請稍後再試: {str(e)}"
            }, status=500)
        

    def get_text_metadata_list(request):
        """
        Input (POST JSON):
        {
            "conversation_uid": <string>
        }

        Output (JsonResponse):
        {
            "status": <bool>,
            "message": <string>,
            "data": [
                {
                    "text_uid": <string>,
                    "text_path": <string>,
                    "created_at": <string>,
                },
                ...
            ]
        }
        """
        try:
            # 1. 解析 JSON payload
            payload = json.loads(request.body)

            # 2. 檢查必填欄位
            if "conversation_uid" not in payload:
                return JsonResponse({
                    "status": False,
                    "message": "缺少必填欄位: conversation_uid"
                }, status=400)

            # 3. 呼叫 Controller 查詢並回傳結果
            response = TextController.get_text_list_by_conversation(payload["conversation_uid"])

            # 統一回傳格式
            return JsonResponse({
                "status": response["status"],
                "message": response["message"],
                "data": response.get("data", [])
            }, status=response["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({
                "status": False,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"系統發生錯誤，請稍後再試: {str(e)}"
            }, status=500)
        
    def delete_text_metadata(request):
        """
        Input (POST JSON):
        {
            "text_uid": <uid>
        }

        Output (JsonResponse):
        {
            "status": <bool>,
            "message": <string>
        }
        """
        try:
            # 1) 解析 JSON
            payload = json.loads(request.body)

            # 2) 檢查必填欄位
            if "text_uid" not in payload:
                return JsonResponse({
                    "status": False,
                    "message": "缺少必填欄位: text_uid"
                }, status=400)
            
            # 3) 呼叫 Controller 刪除資料
            response = TextController.delete_text_by_uid(text_uid=text_uid)

            # 4) 統一回傳格式
            return JsonResponse({
                "status": response["status"],
                "message": response["message"]
            }, status=response["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({
                "status": False,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"系統發生錯誤，請稍後再試: {str(e)}"
            }, status=500)