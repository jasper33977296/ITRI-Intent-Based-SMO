import os
import json
import requests
from openai import OpenAI
from main.apps.metadata_mgt.services.ConversationController import ConversationController

from main.utils.logger import log_writer
from main.utils.ApiKit import json_request
from sseclient import SSEClient

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
    


def dify_single_intent_workflow(conversation_uid,user_prompt):
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
    # 建議在必要時把 user_prompt 帶入 payload["query"] 中 (目前示例寫死成 "text")
    # 也可依實際需求調整：payload["inputs"] 等欄位
    api_key = os.getenv("DIFY_API_KEY", "")
    bearer = "Bearer "+api_key

    headers = {
        "Authorization": bearer,
        "Content-Type": "application/json"
    }

    result = ConversationController.get_dify_conversation_id(conversation_uid)
    dify_conversation_id = result.get("data", "")

    payload = {
        "query": user_prompt,
        "inputs": {"conversation_uid": conversation_uid},
        "response_mode": "streaming",
        "user": "test_user1",
        "conversation_id": dify_conversation_id,
        "files": [],
        "auto_generate_name": True
    }
    workflow_finished_data = None
    image_url = "" # 用於儲存圖片 URL

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
        for event in client.events():
            try:
                data = json.loads(event.data)
                node_event = data.get("event", "")
                node_type = data.get("data", {}).get("node_type", "")
                node_title = data.get("data", {}).get("title", "")

                if node_event == "node_finished" and node_type == "answer" and "直接回覆" in node_title:
                    answer = data.get("data", {}).get("outputs", {}).get("answer", "")
                    files_list  = data.get("data", {}).get("outputs", {}).get("files", [])

                    if files_list and isinstance(files_list, list) and len(files_list) > 0:
                        image_url = files_list[0].get("url", "")
                    else:
                        image_url = "" # 如果 files_list 為空或不符合預期，則清空 image_url

                    if image_url != "":
                        text = image_url
                        full_download_url = f"http://{host}{image_url}"
                        work_payload = {
                            "event_type": "2",
                            "conversation_uid": conversation_uid,
                            "text_content": [{
                                "type": "image",
                                "content": full_download_url
                            }],
                        }
                    else:
                        text = answer
                        work_payload = {
                            "event_type": "2",
                            "conversation_uid": conversation_uid,
                            "text_content": [{
                                "type": "message",
                                "content": text
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
                "status": True,
                "message": "成功取得資料",
                "parsed_data": ans_text,             # 可依需求改變資料結構
            }
        else:
            # 如果根本沒有解析到 workflow_finished_data
            return {
                "status": False,
                "message": "未找到 workflow_finished 事件",
                "parsed_data": None,
            }

    except requests.exceptions.Timeout as e:
        return {
            "status": False,
            "message": f"Request Timeout: {str(e)}",
            "parsed_data": None
        }
    except requests.exceptions.RequestException as e:
        # 包含所有 requests 模組可能出現的網路錯誤 (ConnectionError, HTTPError 等)
        return {
            "status": False,
            "message": f"HTTP/Network Error: {str(e)}",
            "parsed_data": None
        }
    except Exception as e:
        # 其他非 requests 相關的意外錯誤
        return {
            "status": False,
            "message": f"Unexpected Error: {str(e)}",
            "parsed_data": None
        }