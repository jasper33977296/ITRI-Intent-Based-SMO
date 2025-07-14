import os
import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from main.utils.FileKit import delete_file, delete_folder
from main.utils.ApiKit import json_request
from main.utils.logger import log_trigger
from main.apps.metadata_mgt.services.UserController import UserController

class UserManager:
    """
    提供對 User Model 進行 Create / Read / Update / Delete 的方法，
    並使用 UserController 進行業務邏輯處理。
    """

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def hello_world(request):
        try:
            return JsonResponse({
                "status_code": 200,
                "status": True,
                "message": "Hello World"
            }, status=200)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "status": False,
                "message": "系統發生錯誤，請稍後再試"
            }, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def create_user(request):
        """
        建立新使用者。
        """
        try:
            payload = json.loads(request.body)

            # 必填欄位檢查
            required_fields = ["user_uname", "user_password", "user_uemail"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"缺少必填欄位: {', '.join(missing_fields)}"
                }, status=400)

            # 呼叫 Controller 建立
            response = UserController.create_user(
                user_uname=payload['user_uname'],
                user_password=payload['user_password'],
                user_uemail=payload['user_uemail']
            )

            return JsonResponse(response, status=response["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({
                "status_code": 400,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "message": f"系統發生錯誤，請稍後再試: {str(e)}"
            }, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def login_user(request):
        try:
            payload = json.loads(request.body)

            # 檢查必要欄位
            required_fields = ['user_uname', 'user_password']
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"缺少必填欄位: {', '.join(missing_fields)}"
                }, status=400)

            # 呼叫 Controller 登入邏輯
            response = UserController.login_user(
                user_uname=payload['user_uname'],
                user_password=payload['user_password']
            )

            return JsonResponse(response, status=response["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({
                "status_code": 400,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "message": f"系統發生錯誤，請稍後再試: {str(e)}"
            }, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def get_user(request):
        """
        取得使用者資訊。
        """
        try:
            payload = json.loads(request.body)

            # 必填欄位檢查
            required_fields = ["user_uname"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"缺少必填欄位: {', '.join(missing_fields)}"
                }, status=400)

            # 呼叫 Controller 查詢
            response = UserController.get_user_by_name(payload["user_uname"])

            return JsonResponse(response, status=response["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({
                "status_code": 400,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "message": f"系統發生錯誤，請稍後再試: {str(e)}"
            }, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def update_user(request):
        """
        更新使用者資訊。
        """
        try:
            payload = json.loads(request.body)

            # 必填欄位檢查
            required_fields = ["user_uid"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"缺少必填欄位: {', '.join(missing_fields)}"
                }, status=400)

            update_fields = {k: v for k, v in payload.items() if k != "user_uid"}
            
            # 呼叫 Controller 更新
            response = UserController.update_user(payload.get("user_uid"), **update_fields)

            return JsonResponse(response, status=response["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({
                "status_code": 400,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "message": f"系統發生錯誤，請稍後再試: {str(e)}"
            }, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
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

            # 必填欄位檢查
            required_fields = ["user_uid"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"缺少必填欄位: {', '.join(missing_fields)}"
                }, status=400)
            
            user_uid = payload.get("user_uid")

            # (A) 先取得該 user 的所有 conversation
            try:
                meta_payload = {"user_uid": user_uid}
                resp = json_request(
                    module="metadata_mgt",
                    actor="ConversationManager",
                    function="get_conversation_metadata_list",
                    payload=meta_payload
                )
                conversation_data = resp.json()
            except Exception as e:
                return JsonResponse({
                    "status_code": 500,
                    "message": f"獲取 get_conversation_metadata_list() 失敗: {str(e)}"
                }, status=500)

            if not conversation_data.get("status_code", 400):
                return JsonResponse(conversation_data, status=conversation_data.get("status_code"))

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
                "message": "使用者刪除成功"
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({
                "status_code": 400,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "message": f"系統發生錯誤，請稍後再試: {str(e)}"
            }, status=500)