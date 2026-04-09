import os
import json
import requests

from django.conf import settings
from openai import OpenAI
from sseclient import SSEClient

from main.apps.metadata_mgt.services.ConversationController import ConversationController
from main.apps.metadata_mgt.services.AgentController import AgentController
from main.utils.logger import log_writer
from main.utils.ApiKit import json_request

def text_analysis(user_prompt):
    """
    範例：確認能與 GPT 正常溝通，
    並將結果以 Python dict 回傳給呼叫者 (通常是 WorkflowManager)。

    Params:
        user_prompt (str): 使用者輸入內容
    
    Returns:
        dict: {
            "status": bool,           # True: 成功, False: 失敗
            "message": str,           # 錯誤或說明資訊
            "parsed_data": any,       # 從 GPT 解析出的資料 (若成功)
        }
    """
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY", ""), 
    )
    # System Prompt：示範如何對 GPT 設定指令，如需產生 2D array 代表先後/並行子需求等
    system_prompt = """ 
        你是一個能解析中文多需求(命題)的助理, 能判斷哪些需求可並行(同時).
        請用 2D陣列表示先後順序, 相同陣列表示並行.
    """

    try: 
        # 1. 呼叫 GPT
        chat_completion = client.chat.completions.create(
        messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": f"""{user_prompt}
                                                    請先列出子需求,給id(1,2,3..),再以 "order"=[ [...],[...]] 格式表示先後/並行:
                                                    如:
                                                    {{
                                                    "subneeds":[{{"id":1,"text":"查詢A"}},{{"id":2,"text":"查詢B"}},{{"id":3,"text":"檢查付款"}}],
                                                    "order":[[1,2],[3]]
                                                    }}
                 """},
            ],
            model="gpt-3.5-turbo",
        )
        
        gpt_response = chat_completion.choices[0].message.content.strip()

        return {
            "text_content":[
                {
                "type":"message",
                "content":gpt_response
                }
            ]
        }

    except json.JSONDecodeError:
        # GPT 回傳內容無法被 json.loads() 成為合法 JSON
        return {
            "status": False,
            "message": "GPT 回傳的不是有效 JSON 格式",
            "parsed_data": None,
        }

    except Exception as e:
        return {
            "status": False,
            "message": str(e),
            "parsed_data": None
        }
    

def validate_dify_api_key(api_key: str):
    """
    驗證 Dify API Key 是否可用。
    以 GET http://{HTTP_DIFY_HOST}/v1/info 並帶 Authorization Bearer {api_key} 驗證。

    Returns:
        dict: {"status_code": int, "message": str}
    """
    try:
        host = os.getenv("HTTP_DIFY_HOST", "")
        if not api_key:
            return {"status_code": 400, "message": "缺少 api_key"}
        headers = {"Authorization": f"Bearer {api_key}"}
        resp = requests.get(f"http://{host}/v1/info", headers=headers, timeout=10)
        resp.raise_for_status()
        # 成功則 200
        return {"status_code": 200, "message": "API key valid"}
    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, 'status_code', 500)
        return {"status_code": status, "message": f"HTTPError: {str(e)}"}
    except requests.exceptions.RequestException as e:
        return {"status_code": 500, "message": f"Network error: {str(e)}"}
    except Exception as e:
        return {"status_code": 500, "message": f"Unexpected error: {str(e)}"}


def upload_image_to_dify(image_path, api_key):
    """
    將本地圖片上傳到 Dify /v1/files/upload，取得 upload_file_id。

    Params:
        image_path (str): 本地圖片的絕對路徑
        api_key (str): Dify API Key

    Returns:
        str: upload_file_id，失敗則回傳空字串
    """
    host = os.getenv("HTTP_DIFY_HOST", "")
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        with open(image_path, "rb") as f:
            files = {"file": (os.path.basename(image_path), f, "image/png")}
            data = {"user": "test_user1"}
            resp = requests.post(
                f"http://{host}/v1/files/upload",
                headers=headers,
                files=files,
                data=data,
                timeout=30
            )
            resp.raise_for_status()
            return resp.json().get("id", "")
    except Exception as e:
        print(f"[upload_image_to_dify] Failed: {e}")
        return ""


def build_dify_files(image_items, api_key):
    """
    將 image_items 中的圖片逐一上傳到 Dify，組裝 files 參數。

    Params:
        image_items (list): [{"type": "image", "content": "image_uid"}, ...]
        api_key (str): Dify API Key

    Returns:
        list: Dify chat-messages 的 files 參數
    """
    files = []
    for item in image_items:
        image_uid = item.get("content", "")
        if not image_uid:
            continue

        # 查找本地圖片路徑（遍歷 media/images/ 下所有 conversation 資料夾）
        images_root = os.path.join(settings.MEDIA_ROOT, "images")
        image_path = None
        if os.path.exists(images_root):
            for conv_dir in os.listdir(images_root):
                candidate = os.path.join(images_root, conv_dir, f"{image_uid}.png")
                if os.path.isfile(candidate):
                    image_path = candidate
                    break

        if not image_path:
            print(f"[build_dify_files] Image file not found for image_uid={image_uid}")
            continue

        upload_file_id = upload_image_to_dify(image_path, api_key)
        if upload_file_id:
            files.append({
                "type": "image",
                "transfer_method": "local_file",
                "upload_file_id": upload_file_id
            })

    return files


def dify_single_intent_workflow(conversation_uid, user_prompt, image_items=None):
    """
    並將結果以 Python dict 回傳給呼叫者。

    Params:
        user_prompt (str): 使用者輸入內容
    
    Returns:
        dict: {
            "status": bool,           # True: 成功, False: 失敗
            "message": str,           # 錯誤或說明資訊
            "parsed_data": any,       # 從 GPT 解析出的資料 (若成功，可自行定義為任何資料結構)
        }
    """
    # 1. 透過 AgentController 取得 agent_api_key
    agent_api_result = AgentController.get_agent_api_key_by_conversation(conversation_uid)
    if agent_api_result.get("status_code") != 200:
        return {
            "status_code": 400,
            "message": f"找不到 agent api_key: {agent_api_result.get('message', '')}",
            "parsed_data": None
        }
    
    api_key = agent_api_result.get("data", {}).get("api_key", "")
    bearer = "Bearer " + api_key
    headers = {
        "Authorization": bearer,
        "Content-Type": "application/json"
    }
    result = ConversationController.get_dify_conversation_id(conversation_uid)
    dify_conversation_id = result.get("data", "")

    # 上傳圖片到 Dify 並組裝 files 參數
    dify_files = []
    if image_items:
        dify_files = build_dify_files(image_items, api_key)

    # 將圖片 URL 附加到 query（因為 Dify Agent Strategy plugin 無法接收 files 參數）
    # Plugin 從 query 解析 URL 後建構多模態 UserPromptMessage，Dify 模型層會從 URL 下載圖片
    enriched_query = user_prompt
    if image_items:
        backend_host = os.getenv("HTTP_WORKFLOW_MGT_HOST")
        backend_port = os.getenv("HTTP_WORKFLOW_MGT_PORT")
        api_version = os.getenv("WORKFLOW_MGT_API_VERSION")

        for idx, item in enumerate(image_items):
            image_uid = item.get("content", "")
            if not image_uid:
                continue
            image_url = f"http://{backend_host}:{backend_port}/api/{api_version}/conversation_mgt/ImageManager/serve_image/{image_uid}"
            enriched_query += f"\n[IMAGE_URL_{idx}]{image_url}[/IMAGE_URL_{idx}]"

    payload = {
        "query": enriched_query,
        "inputs": {"conversation_uid": conversation_uid},
        "response_mode": "streaming",
        "user": "test_user1",
        "conversation_id": dify_conversation_id,
        "files": dify_files,
        "auto_generate_name": True
    }
    workflow_finished_data = None
    image_url = "" # 用於儲存圖片 URL
    has_sent_event_2 = False # 用於追蹤是否已發送過 event_type "2"

    try:
        # 1. 呼叫 dify_workflow
        host = os.getenv("HTTP_DIFY_HOST", "")
        response = requests.post(
            f"http://{host}/v1/chat-messages",
            headers=headers,
            json=payload,
            timeout=60,
            stream=True
        )

        # 更新 workflow step & status 2
        work_payload = {
            "conversation_uid": conversation_uid,
            # "workflow_step": "A",
            "workflow_status": "2"
        }

        try:
            resp = json_request(
                module="workflow_mgt",
                actor="WorkflowManager",
                function="update_workflow_status",
                payload=work_payload,
            )
        except Exception as e:
            print("Workflow 更新失敗: ", e)

        # 2. 處理串流回應
        client = SSEClient(response)
        agent_files_list = []  # 從 Agent 節點擷取的 files（Answer 節點可能不帶 files）
        for event in client.events():
            try:
                data = json.loads(event.data)
                node_event = data.get("event", "")
                node_type = data.get("data", {}).get("node_type", "")
                node_title = data.get("data", {}).get("title", "")

                # 從 Agent 節點擷取 files（圖片等）
                if node_event == "node_finished" and node_type == "agent":
                    agent_files = data.get("data", {}).get("outputs", {}).get("files", [])
                    if agent_files and isinstance(agent_files, list):
                        agent_files_list = agent_files

                if node_event == "node_finished" and node_type == "answer" and "直接回覆" in node_title:
                    answer = data.get("data", {}).get("outputs", {}).get("answer", "")
                    files_list  = data.get("data", {}).get("outputs", {}).get("files", [])
                    # 若 Answer 節點沒有 files，使用 Agent 節點的 files
                    if not files_list:
                        files_list = agent_files_list

                    if files_list and isinstance(files_list, list) and len(files_list) > 0:
                        image_url = files_list[0].get("url", "")
                    else:
                        image_url = "" # 如果 files_list 為空或不符合預期，則清空 image_url

                    text = answer
                    text_content = [{"type": "message", "content": answer}]

                    if image_url != "":
                        full_download_url = f"http://{host}{image_url}"
                        text_content.append({"type": "image", "content": full_download_url})

                    work_payload = {
                        "event_type": "2",
                        "conversation_uid": conversation_uid,
                        "text_content": text_content,
                    }

                    try:
                        resp = json_request(
                            module="workflow_mgt",
                            actor="Producer",
                            function="dispatch_topic",
                            payload=work_payload,
                        )
                        has_sent_event_2 = True
                        print("推播成功:", resp)
                    except Exception as e:
                        print("推播失敗:", e)

                elif node_event == "workflow_finished":
                    workflow_finished_data = data
                    break

            except json.JSONDecodeError as e:
                print(f"JSON 解析錯誤: {e}, 原始數據: {event.data}")
            except Exception as e:
                print(f"處理事件時發生錯誤: {e}, 原始數據: {event.data}")

        # 3. 整理解析結果
        if workflow_finished_data:
            dify_conversation_id = workflow_finished_data.get("conversation_id", "")
            ConversationController.update_dify_conversation_id(conversation_uid=conversation_uid, dify_conversation_id=dify_conversation_id)
            ans_text = (
                workflow_finished_data
                .get("data", {})
                .get("outputs", {})
                .get("answer", "未找到 answer")
            )
            if ans_text == "未找到 answer":
                log_writer(
                    log_level="ERROR",
                    status_code="802",
                    source_type="dify engine",
                    func=dify_single_intent_workflow,
                    args=None,
                    message=ans_text
                )
            
            # 更新 workflow step & status 3
            work_payload = {
                "conversation_uid": conversation_uid,
                # "workflow_step": "A",
                "workflow_status": "3"
            }

            try:
                resp = json_request(
                    module="workflow_mgt",
                    actor="WorkflowManager",
                    function="update_workflow_status",
                    payload=work_payload,
                )
                work_data = resp.json()
            except Exception as e:
                print("Workflow 更新失敗: ", e)

            # 判斷 dify 是否發生錯誤
            if not has_sent_event_2:
                work_payload = {
                    "event_type": "0",
                    "conversation_uid": conversation_uid,
                    "text_content": [{
                        "type": "message",
                        "content": "Agent 處理請求失敗，請稍後再試。"
                    }],
                }

                try:
                    resp = json_request(
                        module="workflow_mgt",
                        actor="Producer",
                        function="dispatch_topic",
                        payload=work_payload,
                    )
                    print("推播成功:", resp)
                except Exception as e:
                    print("推播失敗:", e)

            work_payload = {
                "event_type": "3",
                "conversation_uid": conversation_uid,
                "text_content": [{
                    "type": "message",
                    "content": "Finish workflow"
                }],
            }

            try:
                resp = json_request(
                    module="workflow_mgt",
                    actor="Producer",
                    function="dispatch_topic",
                    payload=work_payload,
                )
                print("推播成功:", resp)
            except Exception as e:
                print("推播失敗:", e)

            return {
                "status_code": 200,
                "message": "成功取得資料",
                "data": ans_text,             # 可依需求改變資料結構
            }
        else:
            # 如果根本沒有解析到 workflow_finished_data
            return {
                "status_code": 404,
                "message": "未找到 workflow_finished 事件",
                "data": None,
            }

    except requests.exceptions.Timeout as e:
        return {
            "status_code": 500,
            "message": f"Request Timeout: {str(e)}",
            "data": None
        }
    except requests.exceptions.RequestException as e:
        # 包含所有 requests 模組可能出現的網路錯誤 (ConnectionError, HTTPError 等)
        return {
            "status_code": 500,
            "message": f"HTTP/Network Error: {str(e)}",
            "data": None
        }
    except Exception as e:
        # 其他非 requests 相關的意外錯誤
        return {
            "status_code": 500,
            "message": f"Unexpected Error: {str(e)}",
            "data": None
        }