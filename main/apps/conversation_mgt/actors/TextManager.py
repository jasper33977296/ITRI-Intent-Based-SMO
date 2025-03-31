import os
import json
import base64
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

# Your FileKit helpers
from main.utils.FileKit import (
    append_text_uid_to_csv,
    read_text_uids_from_csv,
    read_text_jsons,
    create_json_file,
    delete_file
)

# Your utility for calling other services
from main.utils.ApiKit import json_request


class TextManager:

    @csrf_exempt
    @require_http_methods(["POST"])
    def create_text(request):
        """
        建立一筆 text 資料 (可能含有多個段落或圖片)。
        
        需求修正：
        1) 檢查請求中的必填欄位（conversation_uid, text_content, role）。
           - text_content 必須是 list，每個元素都需包含 "type" 與 "content"。
        2) 呼叫 metadata_mgt 的 TextManager.create_text_metadata 建立 text metadata，
           從回傳結果中取得 text_uid、user_uid、text_path 等資訊。
        3) 如果 text_content 裡有 type="image" 的項目：
           - 依序呼叫 metadata_mgt 的 ImageManager.create_image_metadata 建立 image metadata。
           - 解析 base64 後存成 images/{text_uid}/{image_uid}.png。
           - 將該項目的 content 從 base64 編碼置換為 image_uid（未來讀取時再以 image_uid 找圖）。
        4) 將該 text_uid 寫入 conversations/{user_uid}/{conversation_uid}.csv (FileKit.append_text_uid_to_csv)。
        5) 建立 texts/{conversation_uid}/{text_uid}.json，內含 role、text_content (已替換掉 base64)。
        6) 回傳包含 text_uid 等資訊的成功訊息。
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

            if not isinstance(text_array, list):
                return JsonResponse({
                    "status": False,
                    "message": "Field 'text_content' must be a list"
                }, status=400)

            for item in text_array:
                if not isinstance(item, dict) or "type" not in item or "content" not in item:
                    return JsonResponse({
                        "status": False,
                        "message": "Each element in 'text_content' must have 'type' and 'content'"
                    }, status=400)

            # (2) 先呼叫 metadata_mgt 建立 text metadata
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
                    "message": f"Fail to call metadata_mgt (create_text_metadata): {str(e)}"
                }, status=502)

            if not meta_data.get("status", False):
                # 後端若有回傳 status_code 以其為主，否則預設 400
                return JsonResponse(meta_data, status=meta_data.get("status_code", 400))

            data_part = meta_data.get("data", {})
            text_uid = data_part.get("text_uid")
            conversation_uid = data_part.get("conversation_uid")  # 後端回傳最新值
            user_uid = data_part.get("user_uid")  # 假設後端會回傳 user_uid
            text_path = data_part.get("text_path")  # e.g. "texts/{conversation_uid}/{text_uid}.json"

            if not text_uid or not conversation_uid or not text_path or not user_uid:
                return JsonResponse({
                    "status": False,
                    "message": "Missing data in metadata response (need text_uid, conversation_uid, user_uid, text_path)"
                }, status=400)

            # 針對 text_content，若有圖片 (type="image")，需分別呼叫 create_image_metadata
            # 並將 base64 內容寫到 images/{text_uid}/{image_uid}.png
            for item in text_array:
                if item["type"] == "image":
                    # 呼叫 metadata_mgt -> ImageManager -> create_image_metadata
                    image_payload = {"text_uid": text_uid}
                    try:
                        img_resp = json_request(
                            module="metadata_mgt",
                            actor="ImageManager",
                            function="create_image_metadata",
                            payload=image_payload
                        )
                        img_data = img_resp.json()
                    except Exception as e:
                        return JsonResponse({
                            "status": False,
                            "message": f"Fail to call metadata_mgt (create_image_metadata): {str(e)}"
                        }, status=502)

                    if not img_data.get("status", False):
                        return JsonResponse(img_data, status=img_data.get("status_code", 400))

                    image_info = img_data.get("data", {})
                    image_uid = image_info.get("image_uid")
                    image_path = image_info.get("image_path")
                    if not image_uid or not image_path:
                        return JsonResponse({
                            "status": False,
                            "message": "Missing image_uid or image_path from create_image_metadata"
                        }, status=400)

                    # 解碼 base64
                    try:
                        image_binary = base64.b64decode(item["content"])
                    except Exception as e:
                        return JsonResponse({
                            "status": False,
                            "message": f"Invalid base64 image content: {str(e)}"
                        }, status=400)

                    # 寫入檔案 images/{text_uid}/{image_uid}.png
                    # 確保資料夾存在
                    directory = os.path.dirname(image_path)
                    if not os.path.exists(directory):
                        os.makedirs(directory, exist_ok=True)

                    try:
                        with open(image_path, "wb") as f:
                            f.write(image_binary)
                    except Exception as e:
                        return JsonResponse({
                            "status": False,
                            "message": f"Failed to write image file: {str(e)}"
                        }, status=500)

                    # 將 content 改成 image_uid (以便之後 get_text_list 時再轉回 base64)
                    item["content"] = image_uid

            # (3) 將 text_uid 加到 conversations/{user_uid}/{conversation_uid}.csv
            conversation_dir = os.path.join("conversations", user_uid)
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

            # (4) 建立 JSON 檔 texts/{conversation_uid}/{text_uid}.json
            #     裡面包含 role, text_content (圖已轉成 image_uid)
            try:
                create_json_file(text_path, {
                    "role": role,
                    "text_content": text_array
                })
            except Exception as e:
                return JsonResponse({
                    "status": False,
                    "message": f"Failed to create/write text JSON: {str(e)}"
                }, status=500)

            # (5) 回傳結果
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
        - 如果某段 text_content.type = "image", content 其實是 image_uid
          這時要呼叫 metadata_mgt -> ImageManager -> get_image_metadata
          取得 image_path 後讀檔並轉為 base64，再放回 content。
        """
        try:
            payload = json.loads(request.body)
            if "conversation_uid" not in payload:
                return JsonResponse({
                    "status": False,
                    "message": "Missing required field: conversation_uid"
                }, status=400)

            conversation_uid = payload["conversation_uid"]

            # 1) 透過 metadata_mgt 拿到 conversation_path (CSV 檔路徑)
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
                    "message": f"Fail to call metadata_mgt (get_conversation_metadata): {str(e)}"
                }, status=502)

            if not get_meta_data.get("status", False):
                return JsonResponse(get_meta_data, status=get_meta_data.get("status_code", 400))

            conversation_path = get_meta_data["data"].get("conversation_path")
            if not conversation_path:
                return JsonResponse({
                    "status": False,
                    "message": "conversation_path not found in metadata"
                }, status=400)

            # 2) 讀取 CSV 檔中的所有 text_uid
            try:
                text_uids = read_text_uids_from_csv(conversation_path)
            except Exception as e:
                return JsonResponse({
                    "status": False,
                    "message": f"Failed to read CSV: {str(e)}"
                }, status=500)

            # 3) 讀取各 text JSON (含 role, text_content)
            try:
                data_list = read_text_jsons(conversation_uid, text_uids)
            except Exception as e:
                return JsonResponse({
                    "status": False,
                    "message": f"Failed to read text JSONs: {str(e)}"
                }, status=500)

            # 4) 若 text_content 內有 type="image", content= image_uid
            #    則呼叫 ImageManager -> get_image_metadata, 拿到 image_path 後讀檔並 base64 編碼
            for text_item in data_list:
                text_content = text_item.get("text_content", [])
                for block in text_content:
                    if block.get("type") == "image":
                        image_uid = block.get("content")
                        if not image_uid:
                            continue

                        # 呼叫 image metadata
                        try:
                            img_resp = json_request(
                                module="metadata_mgt",
                                actor="ImageManager",
                                function="get_image_metadata",
                                payload={"image_uid": image_uid}
                            )
                            img_data = img_resp.json()
                        except Exception as e:
                            return JsonResponse({
                                "status": False,
                                "message": f"Fail to call metadata_mgt (get_image_metadata): {str(e)}"
                            }, status=502)

                        if not img_data.get("status", False):
                            # 留下錯誤訊息，但可繼續其他 block
                            block["content"] = f"[Error: {img_data.get('message', 'Unknown error')}]"
                            continue

                        image_path = img_data["data"].get("image_path")
                        if not image_path or not os.path.exists(image_path):
                            block["content"] = "[Error: image file not found]"
                            continue

                        # 讀檔 -> base64
                        try:
                            with open(image_path, "rb") as f:
                                raw_data = f.read()
                            encoded_str = base64.b64encode(raw_data).decode("utf-8")
                            block["content"] = encoded_str
                        except Exception as e:
                            block["content"] = f"[Error reading image: {str(e)}]"

            # 5) 回傳最終整理後的 data_list
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
        - 同時刪除該 text 下所有 image (若有)
        """
        try:
            payload = json.loads(request.body)
            if "text_uid" not in payload:
                return JsonResponse({
                    "status": False,
                    "message": "Missing required field: text_uid"
                }, status=400)

            text_uid = payload["text_uid"]

            # 1) 先查詢 text_path
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
                    "message": f"Fail to call metadata_mgt (get_text_metadata): {str(e)}"
                }, status=502)

            if not get_meta_data.get("status", False):
                return JsonResponse(get_meta_data, status=get_meta_data.get("status_code", 400))

            text_path = get_meta_data["data"].get("text_path")
            if not text_path:
                return JsonResponse({
                    "status": False,
                    "message": "text_path not found in metadata"
                }, status=400)

            # 2) 讀取該 text JSON，若有 type="image"，則刪除 image_metadata + 檔案
            #    (透過 ImageManager.delete_image_metadata)
            #    注意：若一個 text 裡有多張圖片都要刪除
            if os.path.exists(text_path):
                try:
                    with open(text_path, "r", encoding="utf-8") as f:
                        text_data = json.load(f)
                except Exception as e:
                    return JsonResponse({
                        "status": False,
                        "message": f"Failed to read JSON file: {str(e)}"
                    }, status=500)

                text_content = text_data.get("text_content", [])
                for block in text_content:
                    if block.get("type") == "image":
                        image_uid = block.get("content")
                        if not image_uid:
                            continue
                        # 呼叫 ImageManager -> delete_image_metadata
                        try:
                            del_resp = json_request(
                                module="metadata_mgt",
                                actor="ImageManager",
                                function="delete_image_metadata",
                                payload={"image_uid": image_uid}
                            )
                            del_data = del_resp.json()
                            # 如果刪除失敗，可考慮記錄
                        except Exception as e:
                            # 可選擇直接返回錯誤，或僅印出警告
                            return JsonResponse({
                                "status": False,
                                "message": f"Fail to delete image metadata: {str(e)}"
                            }, status=502)

            # 3) 最後刪除 text_uid.json 檔
            try:
                delete_file(text_path)
            except Exception as e:
                return JsonResponse({
                    "status": False,
                    "message": f"Failed to remove text JSON file: {str(e)}"
                }, status=500)

            # ※ 如果還需呼叫 metadata_mgt -> delete_text_metadata，可在此呼叫
            #    e.g.:
            #    del_text_resp = json_request(
            #        module="metadata_mgt",
            #        actor="TextManager",
            #        function="delete_text_metadata",
            #        payload={"text_uid": text_uid}
            #    )

            return JsonResponse({
                "status": True,
                "message": "Text deleted"
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"status": False, "message": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"status": False, "message": str(e)}, status=500)
