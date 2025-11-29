import os
import re
import json
import base64
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from main.utils.logger import log_trigger

from main.apps.conversation_mgt.services.ConversationKit import generate_conversation_title

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
    @log_trigger()
    def create_text(request):
        """
        建立一筆 text 資料 (可能含有多個段落或圖片)。

        1) 檢查請求中的必填欄位（conversation_uid, text_content, role）。
        - text_content 必須是 list，每個元素都需包含 "type" 與 "content"。
        2) 呼叫 metadata_mgt 的 TextManager.create_text_metadata 建立 text metadata，
        從回傳結果中取得 text_uid、user_uid、text_path 等資訊。
        3) 將該 text_uid 寫入 conversations/{user_uid}/{conversation_uid}.csv。
        4) 建立 texts/{conversation_uid}/{text_uid}.json，內含 role、text_content (已替換掉 base64)。
        5) 回傳包含 text_uid 等資訊的成功訊息。
        """
        try:
            payload = json.loads(request.body)

            # (1) 檢查必填欄位
            required_fields = ["conversation_uid", "text_content", "role"]
            missing = [f for f in required_fields if f not in payload]
            if missing:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"Missing required fields: {', '.join(missing)}"
                }, status=400)

            conversation_uid = payload["conversation_uid"]
            text_array = payload["text_content"]
            role = payload["role"]
            retry = payload.get("retry")

            if not isinstance(text_array, list):
                return JsonResponse({
                    "status_code": 400,
                    "message": "Field 'text_content' must be a list"
                }, status=400)

            for item in text_array:
                if not isinstance(item, dict) or "type" not in item or "content" not in item:
                    return JsonResponse({
                        "status_code": 400,
                        "message": "Each element in 'text_content' must have 'type' and 'content'"
                    }, status=400)

            # 提前獲取對話 metadata，用於後續判斷
            try:
                conv_meta_resp = json_request(
                    module="metadata_mgt",
                    actor="ConversationManager",
                    function="get_conversation_metadata",
                    payload={"conversation_uid": conversation_uid},
                )
                conv_meta_data = conv_meta_resp.json()
            except Exception as e:
                return JsonResponse({
                    "status_code": 502,
                    "message": f"Fail to call metadata_mgt (get_conversation_metadata): {str(e)}"
                }, status=502)

            if not conv_meta_data.get("status_code", 400):
                return JsonResponse(conv_meta_data, status=conv_meta_data.get("status_code", 400))
            # **[優化]** 將標題生成邏輯移出迴圈，僅在需要時執行一次

            conversation_name = conv_meta_data.get("data","").get("conversation_name","")

            if conversation_name == "":
                user_prompt_for_title = ""
                for item in text_array:
                    if item.get("type") == "message" and isinstance(item.get("content"), str):
                        user_prompt_for_title = item['content']
                        
                        try:
                            conversation_name = generate_conversation_title(user_prompt=user_prompt_for_title)

                            json_request(
                                module="metadata_mgt",
                                actor="ConversationManager",
                                function="update_conversation_name",
                                payload={
                                    "conversation_uid": conversation_uid,
                                    "conversation_name": conversation_name
                                },
                            )
                            # 這裡可以選擇性地檢查更新是否成功，若失敗可記錄 log
                        except Exception as e:
                            # 即使更新標題失敗，主流程可能仍需繼續，故僅記錄警告
                            print(f"Warning: Failed to update conversation name for {conversation_uid}: {e}")
                        break  # 找到第一個就足夠

            # **[優化]** 獨立迴圈，專門處理內容清理
            pattern = re.compile(r'\s*\{\s*"reason"\s*:\s*".*?"\s*\}', re.DOTALL)
            for item in text_array:
                if isinstance(item.get('content'), str):
                    item['content'] = pattern.sub('', item['content'])

            # 判斷 type == image 創建 image
            for item in text_array:
                if item.get("type") == "image":
                    meta_payload = {
                        "conversation_uid": conversation_uid,
                        "content": item.get("content")
                    }

                    try:
                        resp = json_request(
                            module="conversation_mgt",
                            actor="ImageManager",
                            function="create_image",
                            payload=meta_payload
                        )
                        result = resp.json()

                        if result.get("status_code") != 201:
                            return JsonResponse(result, status=result.get("status_code", 400))

                        image_uid = result.get("data", {}).get("image_uid")
                        if not image_uid:
                            return JsonResponse({
                                "status_code": 500,
                                "message": f"image_uid 不存在於回傳值中: {result}"
                            }, status=500)

                        item["content"] = image_uid

                    except Exception as e:
                        return JsonResponse({
                            "status_code": 500,
                            "message": f"Failed to create image metadata: {str(e)}"
                        }, status=500)

            # (2) 呼叫 metadata_mgt 建立 text metadata
            try:
                text_meta_resp = json_request(
                    module="metadata_mgt",
                    actor="TextManager",
                    function="create_text_metadata",
                    payload={"conversation_uid": conversation_uid},
                )
                text_meta_data = text_meta_resp.json()
            except Exception as e:
                return JsonResponse({
                    "status_code": 502,
                    "message": f"Fail to call metadata_mgt (create_text_metadata): {str(e)}"
                }, status=502)

            if not text_meta_data.get("status_code", 400):
                return JsonResponse(text_meta_data, status=text_meta_data.get("status_code", 400))

            data_part = text_meta_data.get("data", {})
            text_uid = data_part.get("text_uid")
            user_uid = data_part.get("user_uid")
            text_path = data_part.get("text_path")

            if not all([text_uid, user_uid, text_path]):
                return JsonResponse({
                    "status_code": 500,
                    "message": "Missing critical data in metadata response (need text_uid, user_uid, text_path)"
                }, status=500) # 使用 500，因為這是後端服務間的契約問題

            # (3) 將 text_uid 加到 conversations/{user_uid}/{conversation_uid}.csv
            conversation_dir = os.path.join("conversations", user_uid)
            os.makedirs(conversation_dir, exist_ok=True)
            conversation_csv_path = os.path.join(conversation_dir, f"{conversation_uid}.csv")
            try:
                append_text_uid_to_csv(conversation_csv_path, text_uid)
            except Exception as e:
                # 考慮補償交易：若此步失敗，是否應刪除剛建立的 text metadata？
                return JsonResponse({
                    "status_code": 500,
                    "message": f"Failed to append text_uid to CSV: {str(e)}"
                }, status=500)

            # (4) 建立 JSON 檔 texts/{...}/{text_uid}.json
            try:
                json_data = {
                    "role": role,
                    "text_content": text_array,
                    "reward": ""
                }
                if retry is not None:
                    json_data["retry"] = retry
                    
                create_json_file(text_path, json_data)
            except Exception as e:
                return JsonResponse({
                    "status_code": 500,
                    "message": f"Failed to create/write text JSON: {str(e)}"
                }, status=500)

            # (5) 回傳結果
            return JsonResponse({
                "status_code": 201,
                "message": "Text created successfully",
                "data": {
                    "text_uid": text_uid
                }
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"status_code": 400, "message": "Invalid JSON"}, status=400)
        except Exception as e:
            # 捕捉所有其他未預期的錯誤
            return JsonResponse({"status_code": 500, "message": str(e)}, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def get_text_list(request):
        """
        取得指定對話的所有 text 資料列表，流程如下：

        1) 從傳入的 conversation_uid 呼叫 metadata_mgt -> ConversationManager.get_conversation_metadata，
           取得 conversation_path (CSV 路徑)。
        2) 讀取該 CSV，取得所有 text_uid。
        3) 以每個 text_uid 到 texts/{conversation_uid}/{text_uid}.json 讀取對應的 text 資料。
        4) 若 text_content 裡有 type="image" 且 content = image_uid，就呼叫 metadata_mgt -> ImageManager.get_image_metadata
           拿到 image_path 後讀檔、轉 base64，並置回 content。
        5) 最後回傳所有 text 資料。
        """
        try:
            payload = json.loads(request.body)
            if "conversation_uid" not in payload:
                return JsonResponse({
                    "status_code": 400,
                    "message": "Missing required field: conversation_uid"
                }, status=400)

            conversation_uid = payload["conversation_uid"]

            # (1) 透過 metadata_mgt 拿到 conversation_path (CSV 檔路徑)
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
                    "status_code": 502,
                    "message": f"Fail to call metadata_mgt (get_conversation_metadata): {str(e)}"
                }, status=502)

            if not get_meta_data.get("status_code", 400):
                return JsonResponse(get_meta_data, status=get_meta_data.get("status_code", 400))

            conversation_path = get_meta_data["data"].get("conversation_path")
            if not conversation_path:
                return JsonResponse({
                    "status_code": 400,
                    "message": "conversation_path not found in metadata"
                }, status=400)

            # (2) 讀取 CSV 檔中的所有 text_uid
            try:
                text_uids = read_text_uids_from_csv(conversation_path)
            except Exception as e:
                return JsonResponse({
                    "status_code": 500,
                    "message": f"Failed to read CSV: {str(e)}"
                }, status=500)

            # 如果 conversation_csv 內沒有任何 text_uid，可直接回傳
            if not text_uids:
                return JsonResponse({
                    "status_code": 200,
                    "message": "No text records found in this conversation",
                    "data": []
                }, status=200)

            # (3) 讀取各 text JSON (含 role, text_content)
            try:
                data_list = read_text_jsons(conversation_uid, text_uids)
            except Exception as e:
                return JsonResponse({
                    "status_code": 500,
                    "message": f"Failed to read text JSONs: {str(e)}"
                }, status=500)

            # 防範 data_list 可能為空或無內容
            if not data_list:
                return JsonResponse({
                    "status_code": 200,
                    "message": "No text JSON files found for this conversation",
                    "data": []
                }, status=200)

            # (4) 若 text_content 內有 type="image", content= image_uid
            #    則呼叫 ImageManager -> get_image_metadata, 拿到 image_path 後讀檔並 base64 編碼
            # for text_item in data_list:
            #     text_content = text_item.get("text_content", [])
            #     if not text_content:
            #         # 如果該 text_item 沒有任何內容，可跳過或保留
            #         continue

            #     for block in text_content:
            #         if block.get("type") == "image":
            #             image_uid = block.get("content")
            #             if not image_uid:
            #                 block["content"] = "[Error: empty image_uid]"
            #                 continue

            #             # 呼叫 image metadata
            #             try:
            #                 img_resp = json_request(
            #                     module="metadata_mgt",
            #                     actor="ImageManager",
            #                     function="get_image_metadata",
            #                     payload={"image_uid": image_uid}
            #                 )
            #                 img_data = img_resp.json()
            #             except Exception as e:
            #                 block["content"] = f"[Error calling metadata_mgt for image_uid={image_uid}: {str(e)}]"
            #                 continue

            #             if not img_data.get("status_code", 400):
            #                 # 留下錯誤訊息，但可繼續其他 block
            #                 block["content"] = f"[Error: {img_data.get('message', 'Unknown error')}]"
            #                 continue

            #             image_path = img_data["data"].get("image_path")
            #             if not image_path or not os.path.exists(image_path):
            #                 block["content"] = "[Error: image file not found]"
            #                 continue

            #             # 讀檔 -> base64
            #             try:
            #                 with open(image_path, "rb") as f:
            #                     raw_data = f.read()
            #                 encoded_str = base64.b64encode(raw_data).decode("utf-8")
            #                 block["content"] = encoded_str
            #             except Exception as e:
            #                 block["content"] = f"[Error reading image: {str(e)}]"

            # (5) 回傳最終整理後的 data_list
            return JsonResponse({
                "status_code": 200,
                "message": "Get text list success",
                "data": data_list
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"status_code": 400, "message": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"status_code": 500, "message": str(e)}, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def delete_text(request):
        """
        刪除指定 text，流程如下：

        1) 檢查請求中的 text_uid，呼叫 metadata_mgt -> TextManager.get_text_metadata，取得 text_path。
        2) 讀取該 text JSON，收集所有 image_uid。
        3) 然後逐一呼叫 ImageManager.delete_image 以刪除所有圖檔。
        4) 最後刪除該 text_uid.json 檔案（以及可選擇呼叫 metadata_mgt 刪除 text metadata）。
        5) 回傳刪除成功訊息。
        """
        try:
            payload = json.loads(request.body)
            if "text_uid" not in payload:
                return JsonResponse({
                    "status_code": 400,
                    "message": "Missing required field: text_uid"
                }, status=400)

            text_uid = payload["text_uid"]

            # 1) 查詢 text_path
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
                    "status_code": 502,
                    "message": f"Fail to call metadata_mgt (get_text_metadata): {str(e)}"
                }, status=502)

            if not get_meta_data.get("status_code", 400):
                return JsonResponse(get_meta_data, status=get_meta_data.get("status_code", 400))

            text_path = get_meta_data["data"].get("text_path")
            if not text_path:
                return JsonResponse({
                    "status_code": 400,
                    "message": "text_path not found in metadata"
                }, status=400)

            # 2) 收集所有 image_uid
            image_uids = []
            if os.path.exists(text_path):
                try:
                    with open(text_path, "r", encoding="utf-8") as f:
                        text_data = json.load(f)
                except Exception as e:
                    return JsonResponse({
                        "status_code": 500,
                        "message": f"Failed to read JSON file: {str(e)}"
                    }, status=500)

                text_content = text_data.get("text_content", [])
                for block in text_content:
                    if block.get("type") == "image" and block.get("content"):
                        image_uids.append(block["content"])

            # 3) 呼叫 ImageManager.delete_image 刪除所有圖檔
            for image_uid in image_uids:
                try:
                    del_resp = json_request(
                        module="conversation_mgt",
                        actor="ImageManager",
                        function="delete_image",
                        payload={"image_uid": image_uid}
                    )
                    del_data = del_resp.json()
                    # 如果刪除失敗，可以選擇直接返回錯誤，或紀錄後繼續
                    if not del_data.get("status_code", "200"):
                        return JsonResponse(del_data, status=del_data.get("status_code", 400))
                except Exception as e:
                    return JsonResponse({
                        "status_code": 502,
                        "message": f"Fail to delete image metadata: {str(e)}"
                    }, status=502)

            # 4) 刪除 text_uid.json 檔
            try:
                delete_file(text_path)
            except Exception as e:
                return JsonResponse({
                    "status_code": 500,
                    "message": f"Failed to remove text JSON file: {str(e)}"
                }, status=500)
            
            # 5) 回傳成功
            return JsonResponse({
                "status_code": 200,
                "message": "Text deleted"
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"status_code": 400, "message": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"status_code": 500, "message": str(e)}, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def reward_text(request):
        """
        設定或更新指定 text 的 reward 值（good 或 bad）。

        1) 檢查請求中的必填欄位（conversation_uid, text_uid, reward）。
        2) 驗證 reward 值是否為 "good" 或 "bad"（可以是空字串）。
        3) 讀取 texts/{conversation_uid}/{text_uid}.json。
        4) 更新 reward 欄位並寫回檔案。
        5) 回傳更新成功訊息。
        """
        try:
            payload = json.loads(request.body)

            # (1) 檢查必填欄位
            required_fields = ["conversation_uid", "text_uid", "reward"]
            missing = [f for f in required_fields if f not in payload]
            if missing:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"Missing required fields: {', '.join(missing)}"
                }, status=400)

            conversation_uid = payload["conversation_uid"]
            text_uid = payload["text_uid"]
            reward = payload["reward"]

            # (2) 驗證 reward 值
            if reward not in ["", "good", "bad"]:
                return JsonResponse({
                    "status_code": 400,
                    "message": "Field 'reward' must be empty string, 'good', or 'bad'"
                }, status=400)

            # (3) 讀取 text JSON 檔案
            text_path = os.path.join("texts", conversation_uid, f"{text_uid}.json")
            if not os.path.exists(text_path):
                return JsonResponse({
                    "status_code": 404,
                    "message": f"Text file not found: {text_path}"
                }, status=404)

            try:
                with open(text_path, "r", encoding="utf-8") as f:
                    text_data = json.load(f)
            except Exception as e:
                return JsonResponse({
                    "status_code": 500,
                    "message": f"Failed to read text JSON: {str(e)}"
                }, status=500)

            # (4) 更新 reward 欄位
            text_data["reward"] = reward

            try:
                with open(text_path, "w", encoding="utf-8") as f:
                    json.dump(text_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                return JsonResponse({
                    "status_code": 500,
                    "message": f"Failed to update text JSON: {str(e)}"
                }, status=500)

            # (5) 回傳成功
            return JsonResponse({
                "status_code": 200,
                "message": "Text reward success"
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"status_code": 400, "message": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"status_code": 500, "message": str(e)}, status=500)
        