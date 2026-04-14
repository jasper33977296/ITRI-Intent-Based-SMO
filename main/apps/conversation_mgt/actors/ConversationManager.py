import os
import json
import uuid
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from main.utils.FileKit import  create_empty_csv ,delete_folder ,delete_file ,read_text_uids_from_csv
from main.utils.ApiKit import  json_request
from main.utils.logger import log_trigger


class ConversationManager:

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def create_conversation(request):
        """
        建立一個新的對話檔案 (CSV):
        Input JSON: {
            "user_uid": "...",
            "agent_uid": "..."
        }
        流程:
        1) 從前端取出 user_uid, agent_uid
        2) 呼叫 metadata_mgt API 建立 conversation metadata, 取得 conversation_uid
        3) 呼叫 metadata_mgt API 建立 workflow metadata
        4) 建立一個空的 CSV 檔(只含表頭 "text_uid")
        5) 在 Broker 註冊 topic
        """
        try:
            payload = json.loads(request.body)

            # 必填欄位檢查
            required_fields = ["user_uid", "agent_uid"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"缺少必填欄位: {', '.join(missing_fields)}"
                }, status=400)

            user_uid = payload["user_uid"]
            agent_uid = payload["agent_uid"]

            # 2) 呼叫 metadata_mgt API: 建立 conversation metadata, 並取得 conversation_uid
            meta_payload = {
                "user_uid": user_uid,
                "agent_uid": agent_uid,
                "conversation_name": ''
            }
            try:
                resp = json_request(
                    module="metadata_mgt",
                    actor="ConversationManager",
                    function="create_conversation_metadata",
                    payload=meta_payload,
                )
                meta_data = resp.json()
            except Exception as e:
                return JsonResponse({
                    "status_code": 500,
                    "message": f"Fail to call metadata_mgt API: {str(e)}"
                }, status=502)

            if not meta_data.get("status_code", 400):
                return JsonResponse(meta_data, status=meta_data.get("status_code", 400))

            conversation_uid = meta_data["data"]["conversation_uid"]
            csv_path = meta_data["data"]["conversation_path"]

            # 3) 呼叫 metadata_mgt API: 建立 workflow metadata ===
            workflow_payload = {
                "conversation_uid": conversation_uid
            }
            try:
                workflow_resp = json_request(
                    module="metadata_mgt",
                    actor="WorkflowManager",
                    function="create_workflow_metadata",
                    payload=workflow_payload,
                )
                workflow_data = workflow_resp.json()
            except Exception as e:
                return JsonResponse({
                    "status_code": 500,
                    "message": f"Fail to call workflow metadata API: {str(e)}"
                }, status=502)

            # 確認回傳結果是否成功
            if not workflow_data.get("status_code", 400):
                return JsonResponse(workflow_data, status=workflow_data.get("status_code", 400))

            # 4) 建立一個只含表頭 "text_uid" 的空白 CSV 檔
            try:
                create_empty_csv(csv_path)
            except Exception as e:
                return JsonResponse({
                    "status_code": 500,
                    "message": f"Failed to create CSV file: {str(e)}"
                }, status=500)

            # 5) 在 Broker 註冊 Topic
            try:
                topic_payload = {
                    "conversation_uid": conversation_uid
                }
                resp_topic = json_request(
                    module="topic_mgt",
                    actor="TopicManager",
                    function="create_topic",
                    payload=topic_payload,
                )
                topic_data = resp_topic.json()
                if not topic_data.get("status_code", 201):
                    return JsonResponse(topic_data, status=topic_data.get("status_code", 400))
            except Exception as e:
                return JsonResponse({
                    "status_code": 500,
                    "message": f"Failed to register topic (topic_mgt) : {str(e)}"
                }, status=500)

            # 全部成功
            return JsonResponse({
                "status_code": 201,
                "message": "Conversation created locally (CSV) and workflow metadata created",
                "data": {
                    "conversation_uid": conversation_uid
                }
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"status_code": 400, "message": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"status_code": 500, "message": str(e)}, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def get_conversation_list(request):
        """
        取得指定使用者的所有對話清單
        Input JSON:
            {
                "user_uid": "..."
            }

        流程:
        1) 檢查 payload（必填欄位 user_uid）
        2) 呼叫 metadata_mgt API 取得所有 conversation 的 conversation_uid 與 conversation_name
        3) 回傳結果
        """
        try:
            payload = json.loads(request.body)

            # 1) 必填欄位檢查
            required_fields = ["user_uid"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"缺少必填欄位: {', '.join(missing_fields)}"
                }, status=400)

            user_uid = payload["user_uid"]

            # 2) 呼叫 metadata_mgt API，取得對話清單
            meta_payload = {
                "user_uid": user_uid
            }
            try:
                resp = json_request(
                    module="metadata_mgt",
                    actor="ConversationManager",
                    function="get_conversation_metadata_list",
                    payload=meta_payload,
                )
                meta_data = resp.json()
            except Exception as e:
                return JsonResponse({
                    "status_code": 502,
                    "message": f"Fail to call metadata_mgt API: {str(e)}"
                }, status=502)

            if not meta_data.get("status_code", 400):
                # 如果 metadata API 回傳 status = False，直接將其回傳
                return JsonResponse(meta_data, status=meta_data.get("status_code", 400))

            # 3) 回傳取得的對話清單
            return JsonResponse({
                "status_code": 200,
                "message": "Get conversation list success",
                "data": meta_data.get("data", [])
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"status_code": 400, "message": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"status_code": 500, "message": str(e)}, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def delete_conversation(request):
        """
        刪除指定對話:
        1) 檢查必填欄位 conversation_uid
        2) 透過 metadata_mgt 取得 CSV 路徑、user_uid
        3) 讀取 CSV 檔取得所有 text_uid
        4) 逐一呼叫 TextManager.delete_text (每個 text 會同時刪除其 image metadata + 圖檔)
        5) 呼叫 metadata_mgt 刪除 conversation metadata
        6) 刪除整個 texts/{conversation_uid} 資料夾 (已空，但保險刪除)
        7) 刪除 conversations/{user_uid}/{conversation_uid}.csv
        8) 呼叫 topic_mgt: delete_topic
        """
        try:
            payload = json.loads(request.body)

            # 1) 必填欄位檢查
            required_fields = ["conversation_uid"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"缺少必填欄位: {', '.join(missing_fields)}"
                }, status=400)
            
            conversation_uid = payload["conversation_uid"]

            # 2) 呼叫 metadata_mgt: get_conversation_metadata
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
                    "message": f"Fail to call metadata_mgt API (get_conversation_metadata): {str(e)}"
                }, status=502)

            if not get_meta_data.get("status_code", 400):
                return JsonResponse(get_meta_data, status=get_meta_data.get("status_code", 400))

            # 取得 CSV 路徑與 user_uid
            conversation_path = get_meta_data["data"].get("conversation_path")
            user_uid = get_meta_data["data"].get("user_uid")
            if not conversation_path or not user_uid:
                return JsonResponse({
                    "status_code": 400,
                    "message": "conversation_path or user_uid not found in metadata"
                }, status=400)

            # 3) 讀取 CSV，取得所有 text_uid
            try:
                text_uids = read_text_uids_from_csv(conversation_path)
            except Exception as e:
                return JsonResponse({
                    "status_code": 500,
                    "message": f"Failed to read CSV file: {str(e)}"
                }, status=500)

            # 4) 逐一刪除每個 text_uid （會連帶刪除 image metadata 與檔案）
            for text_uid in text_uids:
                delete_text_payload = {"text_uid": text_uid}
                try:
                    resp_del_text = json_request(
                        module="conversation_mgt",  # or "metadata_mgt", depending on your architecture
                        actor="TextManager",
                        function="delete_text",
                        payload=delete_text_payload,
                    )
                    del_text_data = resp_del_text.json()
                except Exception as e:
                    return JsonResponse({
                        "status_code": 502,
                        "message": f"Fail to call delete_text for text_uid={text_uid}: {str(e)}"
                    }, status=502)

                if not del_text_data.get("status_code", 400):
                    # 即使某個 text 刪除失敗，可選擇直接中斷或繼續嘗試刪除其他 text
                    return JsonResponse(del_text_data, status=del_text_data.get("status_code", 400))
            
            # 5) 清理孤兒圖片：刪除 media/images/{conversation_uid}/ 整個資料夾
            try:
                from django.conf import settings
                image_dir = os.path.join(settings.MEDIA_ROOT, "images", conversation_uid)
                delete_folder(image_dir)
            except Exception as e:
                # 圖片資料夾可能不存在（該對話從未有圖片），不阻斷主流程
                print(f"Warning: Failed to delete image folder for {conversation_uid}: {e}")

            # 6) 清理孤兒音檔：刪除 media/audios/{conversation_uid}/ 整個資料夾
            try:
                from django.conf import settings
                audio_dir = os.path.join(settings.MEDIA_ROOT, "audios", conversation_uid)
                delete_folder(audio_dir)
            except Exception as e:
                # 音訊資料夾可能不存在（該對話從未有音訊），不阻斷主流程
                print(f"Warning: Failed to delete audio folder for {conversation_uid}: {e}")

            # 7) 呼叫 metadata_mgt: delete_conversation_metadata
            try:
                resp_del = json_request(
                    module="metadata_mgt",
                    actor="ConversationManager",
                    function="delete_conversation_metadata",
                    payload=meta_payload,
                )
                del_meta_data = resp_del.json()
            except Exception as e:
                return JsonResponse({
                    "status_code": 502,
                    "message": f"Fail to call metadata_mgt API (delete_conversation_metadata): {str(e)}"
                }, status=502)

            if not del_meta_data.get("status_code", 400):
                return JsonResponse(del_meta_data, status=del_meta_data.get("status_code", 400))

            # 8) 刪除 texts/{conversation_uid} 資料夾 (若裡面已空則快; 若有殘留檔案也能清掉)
            try:
                text_dir = os.path.join("texts", conversation_uid)
                delete_folder(text_dir)
            except Exception as e:
                return JsonResponse({
                    "status_code": 500,
                    "message": f"Failed to remove folder texts/{conversation_uid}: {str(e)}"
                }, status=500)

            # 9) 刪除 conversations/{user_uid}/{conversation_uid}.csv
            try:
                delete_file(conversation_path)
            except Exception as e:
                return JsonResponse({
                    "status_code": 500,
                    "message": f"Failed to remove CSV file: {str(e)}"
                }, status=500)

            # 10) 呼叫 topic_mgt: delete_topic
            try:
                resp_del = json_request(
                    module="topic_mgt",
                    actor="Broker",
                    function="delete_topic",
                    payload=meta_payload,
                )
                del_meta_data = resp_del.json()
            except Exception as e:
                return JsonResponse({
                    "status_code": 502,
                    "message": f"Fail to call topic_mgt API (delete_topic): {str(e)}"
                }, status=502)

            if not del_meta_data.get("status_code", 400):
                return JsonResponse(del_meta_data, status=del_meta_data.get("status_code", 400))

            # 全部成功
            return JsonResponse({
                "status_code": 200,
                "message": "Conversation deleted"
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"status_code": 400, "message": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"status_code": 500, "message": str(e)}, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def get_agent_conversation_list(request):
        """
        取得指定 agent 的所有對話清單
        Input JSON:
            {
                "user_uid": "...",
                "agent_uid": "..."
            }
        流程:
        1) 檢查 payload（必填欄位 user_uid, agent_uid）
        2) 呼叫 metadata_mgt API 取得所有 conversation 的 conversation_uid 與 conversation_name
        3) 回傳結果
        """
        try:
            payload = json.loads(request.body)

            # 1) 必填欄位檢查
            required_fields = ["user_uid", "agent_uid"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"缺少必填欄位: {', '.join(missing_fields)}"
                }, status=400)

            user_uid = payload["user_uid"]
            agent_uid = payload["agent_uid"]

            # 2) 呼叫 metadata_mgt API，取得對話清單
            meta_payload = {
                "user_uid": user_uid,
                "agent_uid": agent_uid
            }
            try:
                resp = json_request(
                    module="metadata_mgt",
                    actor="ConversationManager",
                    function="get_conversation_metadata_list",
                    payload=meta_payload,
                )
                meta_data = resp.json()
            except Exception as e:
                return JsonResponse({
                    "status_code": 502,
                    "message": f"Fail to call metadata_mgt API: {str(e)}"
                }, status=502)

            if not meta_data.get("status_code", 400):
                # 如果 metadata API 回傳 status = False，直接將其回傳
                return JsonResponse(meta_data, status=meta_data.get("status_code", 400))

            # 3) 回傳取得的對話清單
            return JsonResponse({
                "status_code": 200,
                "message": "Get agent conversation list success",
                "data": meta_data.get("data", [])
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"status_code": 400, "message": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"status_code": 500, "message": str(e)}, status=500)