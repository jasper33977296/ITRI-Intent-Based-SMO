import os
import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from main.utils.FileKit import delete_file, delete_folder
from main.utils.ApiKit import json_request
from main.utils.logger import log_trigger, log_writer
from main.apps.metadata_mgt.services.UserController import UserController

class UserManager:
    """
    提供對 User Model 進行 Create / Read / Update / Delete 的方法，
    並使用 UserController 進行業務邏輯處理。
    """

    @csrf_exempt
    @log_trigger("INFO")
    @require_http_methods(["POST"])
    def hello_world(request):
        try:
            return JsonResponse({
                "status_code": 200,
                "status": True,
                "message": "Hello World"
            }, status=200)
        except Exception as e:
            # log_writer(log_writer(log_level="ERROR", message=str(e)))
            return JsonResponse({
                "status_code": 500,
                "status": False,
                "message": "系統發生錯誤，請稍後再試"
            }, status=500)

    @csrf_exempt
    @log_trigger("INFO")
    @require_http_methods(["POST"])
    def create_user(request):
        """
        建立新使用者。
        """
        try:
            payload = json.loads(request.body)

            required_fields = ["username", "password", "email"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "status": False,
                    "message": f"缺少必填欄位: {', '.join(missing_fields)}"
                }, status=400)

            response = UserController.create_user(
                user_name=payload['username'],
                user_password=payload['password'],
                user_email=payload['email']
            )

            # log_writer(log_writer(log_level="INFO" if response["status"] else "ERROR", message=response["message"]))

            return JsonResponse(response, status=response["status_code"])

        except json.JSONDecodeError as e:
            # log_writer(log_writer(log_level="ERROR", message=f"JSONDecodeError: {str(e))}")
            return JsonResponse({
                "status_code": 400,
                "status": False,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            # log_writer(log_writer(log_level="ERROR", message=str(e)))
            return JsonResponse({
                "status_code": 500,
                "status": False,
                "message": f"{str(e)}"
            }, status=500)

    @csrf_exempt
    @log_trigger("INFO")
    @require_http_methods(["POST"])
    def login_user(request):
        try:
            payload = json.loads(request.body)

            # 檢查必要欄位
            required_fields = ['username', 'password']
            for field in required_fields:
                if field not in payload:
                    return JsonResponse({
                        "status": "error",
                        "message": f"Missing required field: {field}"
                    }, status=400)

            # 呼叫 Controller 登入邏輯
            response = UserController.login_user(
                username=payload['username'],
                userpassword=payload['password']
            )

            # 使用 Controller 回傳的 status_code 作為 HTTP 回應碼
            return JsonResponse(response, status=response["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({
                "status": "error",
                "message": "Invalid JSON format"
            }, status=400)

        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)

           

    @csrf_exempt
    @log_trigger("INFO")
    @require_http_methods(["POST"])
    def get_user(request):
        """
        取得使用者資訊。
        """
        try:
            payload = json.loads(request.body)
            user_name = payload.get("user_name")
            if not user_name:
                return JsonResponse({
                    "status_code": 400,
                    "status": False,
                    "message": "缺少 user_name"
                }, status=400)

            response = UserController.get_user_by_name(user_name)

            # log_writer(log_writer(log_level="INFO" if response["status"] else "ERROR", message=response["message"]))

            return JsonResponse(response, status=response["status_code"])

        except json.JSONDecodeError as e:
            # log_writer(log_writer(log_level="ERROR", message=f"JSONDecodeError: {str(e))}")
            return JsonResponse({
                "status_code": 400,
                "status": False,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            # log_writer(log_writer(log_level="ERROR", message=str(e)))
            return JsonResponse({
                "status_code": 500,
                "status": False,
                "message": "系統發生錯誤，請稍後再試"
            }, status=500)

    @csrf_exempt
    @log_trigger("INFO")
    @require_http_methods(["POST"])
    def update_user(request):
        """
        更新使用者資訊。
        """
        try:
            payload = json.loads(request.body)
            user_uid = payload.get("user_uid")
            if not user_uid:
                return JsonResponse({
                    "status_code": 400,
                    "status": False,
                    "message": "缺少 user_uid"
                }, status=400)

            update_fields = {
                k: v for k, v in payload.items() if k != "user_uid"
            }
            response = UserController.update_user(user_uid, **update_fields)

            # log_writer(log_writer(log_level="INFO" if response["status"] else "ERROR", message=response["message"]))

            return JsonResponse(response, status=response["status_code"])

        except json.JSONDecodeError as e:
            # log_writer(log_writer(log_level="ERROR", message=f"JSONDecodeError: {str(e))}")
            return JsonResponse({
                "status_code": 400,
                "status": False,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            # log_writer(log_writer(log_level="ERROR", message=str(e)))
            return JsonResponse({
                "status_code": 500,
                "status": False,
                "message": "系統發生錯誤，請稍後再試"
            }, status=500)

    @csrf_exempt
    @log_trigger("INFO")
    @require_http_methods(["POST"])
    def delete_user(request):
        """
        刪除使用者。
        流程：
          1) 先取得該 user_uid 的所有 conversation 資訊 (metadata_mgt)
          2) 逐一刪除對應檔案
          3) 最後呼叫 UserController.delete_user(user_uid)
        """
        try:
            payload = json.loads(request.body)
            user_uid = payload.get("user_uid")
            if not user_uid:
                return JsonResponse({
                    "status_code": 400,
                    "status": False,
                    "message": "缺少 user_uid"
                }, status=400)

            # (A) 先取得該 user 的所有 conversation
            try:
                meta_payload = {"user_uid": user_uid}
                resp = json_request(
                    module="metadata_mgt",
                    actor="ConversationManager",
                    function="get_user_conversation_metadata_list",
                    payload=meta_payload
                    )
                conversation_data = resp.json()
            except Exception as e:
                return JsonResponse({
                    "status_code": 500,
                    "status": False,
                    "message": f"Fail to fetch conversation list from metadata_mgt: {str(e)}"
                }, status=500)

            if not conversation_data.get("status", False):
                return JsonResponse(conversation_data, status=conversation_data.get("status_code", 400))

            # (B) 刪除 conversation 相關檔案
            #     conversation_data["data"] 預期是一個 list，每個元素包含 
            #     { "conversation_uid": "...", "conversation_path": "..." }
            for conv_item in conversation_data.get("data", []):
                conversation_uid = conv_item.get("conversation_uid")
                csv_path        = conv_item.get("conversation_path")

                # 1) 刪除 CSV 檔
                if csv_path and os.path.exists(csv_path):
                    try:
                        delete_file(csv_path)  # or os.remove(csv_path)
                    except Exception as e:
                        print(f"[WARN] Failed to remove CSV file: {csv_path}, error={str(e)}")

                # 2) 刪除 texts/<conversation_uid> 資料夾
                if conversation_uid:
                    texts_dir = os.path.join("texts", conversation_uid)
                    if os.path.exists(texts_dir):
                        try:
                            delete_folder(texts_dir)
                        except Exception as e:
                            print(f"[WARN] Failed to remove texts folder for {conversation_uid}, error={str(e)}")

            # (C) 最後才刪除使用者
            response = UserController.delete_user(user_uid)

            # 如果刪除使用者失敗，回傳錯誤
            if not response.get("status", False):
                return JsonResponse(response, status=response["status_code"])

            # 全部成功
            return JsonResponse({
                "status_code": 200,
                "status": True,
                "message": "User and related conversations have been deleted successfully"
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({
                "status_code": 400,
                "status": False,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "status": False,
                "message": "系統發生錯誤，請稍後再試"
            }, status=500)