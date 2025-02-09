import os
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from main.utils.FileKit import (
    append_text_uid_to_csv,
    read_text_uids_from_csv,
    read_text_jsons,
    create_json_file,
    delete_file
)
from main.utils.ApiKit import json_request

class TextManager:

    @csrf_exempt
    @require_http_methods(["POST"])
    def create_text(request):
        """
        建立一筆 text 內容 (e.g., message, picture, table)。

        流程:
        1) 檢查 payload（必填欄位: conversation_uid, text[], role）
        2) conversation_mgt 呼叫 metadata_mgt 建立 text metadata (create_text_metadata)
        3) 在 conversations/{user_uid}/{conversation_uid}.csv 新增 text_uid  ← *修正路徑*
        4) 建立 texts/{conversation_uid}/{text_uid}.json
        5) 寫入 text 到 {text_uid}.json
        6) 回傳「創建成功」與 text_uid
        """
        try:
            payload = json.loads(request.body)

            # (1) 檢查必填欄位
            required_fields = ["conversation_uid", "text_content", "role"]
            missing = [f for f in required_fields if f not in payload]
            if missing:
                return JsonResponse({
                    "status": False,
                    "message": f"Missing required fields: {', '.join(missing)}"
                }, status=400)

            conversation_uid = payload["conversation_uid"]
            text_array = payload["text_content"]
            role = payload["role"]

            # 檢查 text 是否為 list 且包含 type, content
            if not isinstance(text_array, list):
                return JsonResponse({
                    "status": False,
                    "message": "Field 'text_content' must be an array/list"
                }, status=400)

            for item in text_array:
                if not isinstance(item, dict) or "type" not in item or "content" not in item:
                    return JsonResponse({
                        "status": False,
                        "message": "Each element in 'text' must be an object with 'type' and 'content'"
                    }, status=400)

            # (2) 呼叫 metadata_mgt 建立 text metadata
            meta_payload = {"conversation_uid": conversation_uid}
            try:
                resp = json_request(
                    module="metadata_mgt",
                    actor="TextManager",
                    function="create_text_metadata",
                    payload=meta_payload,
                )
                meta_data = resp.json()
            except Exception as e:
                return JsonResponse({
                    "status": False,
                    "message": f"Fail to call metadata_mgt API (create_text_metadata): {str(e)}"
                }, status=502)

            if not meta_data.get("status", False):
                # 若後端回傳有帶 status_code，可直接使用，否則預設 400
                return JsonResponse(meta_data, status=meta_data.get("status_code", 400))

            data_part = meta_data.get("data", {})
            text_uid = data_part.get("text_uid")
            conversation_uid = data_part.get("conversation_uid")
            user_uid = data_part.get("user_uid")  # 假設後端有回傳 user_uid
            text_path = data_part.get("text_path")  # e.g. "texts/{conversation_uid}/{text_uid}.json"

            # 檢查必須的資訊是否齊全
            if not text_uid or not conversation_uid or not text_path or not user_uid:
                return JsonResponse({
                    "status": False,
                    "message": "Missing data in metadata response (need text_uid, conversation_uid, user_uid, text_path)"
                }, status=400)

            # (3) 在 conversations/{user_uid}/{conversation_uid}.csv 新增 text_uid
            #    路徑範例: conversations/1234-USER-UID/5678-CONVERSATION-UID.csv
            conversation_dir = os.path.join("conversations", user_uid)
            # 若資料夾不存在，先行建立
            if not os.path.exists(conversation_dir):
                os.makedirs(conversation_dir, exist_ok=True)

            conversation_csv_path = os.path.join(conversation_dir, f"{conversation_uid}.csv")
            try:
                append_text_uid_to_csv(conversation_csv_path, text_uid)
            except Exception as e:
                return JsonResponse({
                    "status": False,
                    "message": f"Failed to append text_uid to CSV: {str(e)}"
                }, status=500)

            # (4) 建立 texts/{conversation_uid}/{text_uid}.json，並將 { role, text: [...] } 寫入
            try:
                create_json_file(text_path, {
                    "role": role,
                    "text_content": text_array
                })
            except Exception as e:
                return JsonResponse({
                    "status": False,
                    "message": f"Failed to create/write text JSON file: {str(e)}"
                }, status=500)

            # (6) 回傳只需要「創建成功」以及 text_uid
            return JsonResponse({
                "status": True,
                "message": "Text created successfully",
                "data": {
                    "text_uid": text_uid
                }
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"status": False, "message": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"status": False, "message": str(e)}, status=500)
        
    @csrf_exempt
    @require_http_methods(["POST"])
    def get_text_list(request):
        """
        取得指定對話的所有 text 資料列表:
        Input JSON:
        {
            "conversation_uid": <string>
        }

        流程:
        1) 檢查 payload（必填欄位）
        2) 透過 metadata_mgt API 查詢 {conversation_uid}.csv 路徑
        3) 讀取 CSV 檔 (FileKit.read_text_uids_from_csv)，取得所有 text_uid
        4) 讀取 texts/{conversation_uid}/{text_uid}.json (FileKit.read_text_jsons)
        5) 回傳結果
        """
        try:
            # 1) 解析並檢查必填欄位
            payload = json.loads(request.body)
            if "conversation_uid" not in payload:
                return JsonResponse({
                    "status": False,
                    "message": "Missing required field: conversation_uid"
                }, status=400)

            conversation_uid = payload["conversation_uid"]

            # 2) 呼叫 metadata_mgt API 取得 conversation CSV 路徑
            meta_payload = {"conversation_uid": conversation_uid}
            try:
                resp = json_request(
                    module="metadata_mgt",
                    actor="ConversationManager",
                    function="get_conversation_metadata",
                    payload=meta_payload,
                )
                get_meta_data = resp.json()
            except Exception as e:
                return JsonResponse({
                    "status": False,
                    "message": f"Fail to call metadata_mgt API: {str(e)}"
                }, status=502)

            if not get_meta_data.get("status", False):
                return JsonResponse(get_meta_data, status=get_meta_data.get("status_code", 400))

            conversation_path = get_meta_data["data"].get("conversation_path")
            if not conversation_path:
                return JsonResponse({
                    "status": False,
                    "message": "conversation_path not found in metadata"
                }, status=400)

            # 3) 透過 FileKit 讀取 CSV 中的所有 text_uid
            try:
                text_uids = read_text_uids_from_csv(conversation_path)
            except Exception as e:
                return JsonResponse({
                    "status": False,
                    "message": f"Failed to read CSV file: {str(e)}"
                }, status=500)

            # 4) 讀取 texts/{conversation_uid}/{text_uid}.json (假設已抽離到 read_text_jsons)
            try:
                data_list = read_text_jsons(conversation_uid, text_uids)
            except Exception as e:
                return JsonResponse({
                    "status": False,
                    "message": f"Failed to read text JSONs: {str(e)}"
                }, status=500)

            # 5) 回傳結果
            return JsonResponse({
                "status": True,
                "message": "Get text list success",
                "data": data_list
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"status": False, "message": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"status": False, "message": str(e)}, status=500)
        
    @csrf_exempt
    @require_http_methods(["POST"])
    def delete_text(request):
        """
        刪除指定 text:
        1) 檢查必填欄位 text_uid
        2) 透過 metadata_mgt API 查詢 {text_uid}.json 路徑
        3) 刪除 {text_uid}.json
        """
        try:
            # 1) 解析並檢查必填欄位
            payload = json.loads(request.body)
            if "text_uid" not in payload:
                return JsonResponse({
                    "status": False,
                    "message": "Missing required field: text_uid"
                }, status=400)

            text_uid = payload["text_uid"]

            # 2) 呼叫 metadata_mgt API: get_text_metadata
            #    假設會回傳 { "status": true, "data": { "text_path": "..."} }
            meta_payload = {"text_uid": text_uid}
            try:
                resp = json_request(
                    module="metadata_mgt",
                    actor="TextManager",
                    function="get_text_metadata",
                    payload=meta_payload,
                )
                get_meta_data = resp.json()
            except Exception as e:
                return JsonResponse({
                    "status": False,
                    "message": f"Fail to call metadata_mgt API (get_text_metadata): {str(e)}"
                }, status=502)

            if not get_meta_data.get("status", False):
                return JsonResponse(get_meta_data, status=get_meta_data.get("status_code", 400))

            text_path = get_meta_data["data"].get("text_path")
            if not text_path:
                return JsonResponse({
                    "status": False,
                    "message": "text_path not found in metadata"
                }, status=400)

            # 3) 刪除 {text_uid}.json
            try:
                delete_file(text_path)
            except Exception as e:
                return JsonResponse({
                    "status": False,
                    "message": f"Failed to remove JSON file: {str(e)}"
                }, status=500)

            # 全部成功
            return JsonResponse({
                "status": True,
                "message": "Text deleted"
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"status": False, "message": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"status": False, "message": str(e)}, status=500)