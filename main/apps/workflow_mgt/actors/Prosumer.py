import json
import uuid
import openai
from channels.generic.websocket import AsyncWebsocketConsumer
from main.utils.TextDecorator import text_decorator
from main.utils.ApiKit import json_request_async
from asgiref.sync import sync_to_async
from main.apps.workflow_mgt.services.demo import handle_demo_event ,call_openai
class Prosumer(AsyncWebsocketConsumer):
    """
    Prosumer：
      - 在 connect() 時向 Broker 訂閱 (conversation_uid)，若找不到該 Topic 則關閉連線。
      - 在 disconnect() 時向 Broker 取消訂閱。
      - 在 receive() 中接收前端訊息，依據 event_type 決定要如何處理（如直接回傳或呼叫外部 API）。
      - 在 broker_message() 中處理 Broker 廣播的訊息並回傳給前端。
    """

    async def connect(self):
        """
        1. 從路由中取得 conversation_uid (ws://.../conversation/<conversation_uid>/)。
        2. 檢查話題 (conversation_uid) 是否存在於 Broker；若不存在則拒絕。
        3. 建立隨機 group_name，向 Broker 訂閱。
        4. 接受 WebSocket 連線。
        """
        self.conversation_uid = self.scope["url_route"]["kwargs"].get("conversation_uid")

        # 產生 group_name，避免直接使用 channel_name (可能含非法字元)
        uuid_hex = uuid.uuid4().hex
        self.group_name = f"conv_{uuid_hex}"

        # 假設我們在 Broker 的 "check_conversation" endpoint 以 GET 或 POST 檢查話題是否存在
        try:
            resp = await json_request_async(
                module="topic_mgt",
                actor="TopicManager",
                function="topic_exists",
                payload={"conversation_uid": self.conversation_uid},
            )

            if resp.status_code != 200:
                # 無法正確取得資訊，視為話題不存在或發生錯誤
                await self.close(code=400)
                return

            resp_data = resp.json()
            if not resp_data.get("exists", False):
                # 話題不存在
                await self.close(code=400)
                return

        except Exception as e:
            # 若呼叫 API 失敗，也關閉連線
            print(f"[Prosumer.connect] Failed to check existence via Broker API: {e}")
            await self.close(code=400)
            return

        # 呼叫 Broker API 訂閱
        try:
            resp = await json_request_async(
                module="topic_mgt",
                actor="TopicManager",
                function="subscribe_topic",
                method="POST",
                payload={
                    "conversation_uid": self.conversation_uid,
                    "group_name": self.group_name
                },
            )

            if resp.status_code != 200:
                # 訂閱失敗
                print(f"[Prosumer.connect] Subscribe API failed: {resp.text}")
                await self.close(code=400)
                return

        except Exception as e:
            print(f"[Prosumer.connect] Failed to subscribe via Broker API: {e}")
            await self.close(code=400)
            return

        # 接受 WebSocket 連線
        await self.accept()

    async def disconnect(self, code):
        """
        當 WebSocket 斷線時，向 Broker 取消訂閱。
        """
        # 若未曾成功連線 (conversation_uid 為 None)，可視情況不做任何處理
        if not self.conversation_uid:
            return

        try:
            resp = await json_request_async(
                module="topic_mgt",
                actor="TopicManager",
                function="unsubscribe_topic",
                method="POST",
                payload={
                    "conversation_uid": self.conversation_uid,
                    "group_name": self.group_name
                },
            )
            if resp.status_code != 200:
                # 取消訂閱失敗，僅記錄
                print(f"[Prosumer.disconnect] Unsubscribe API failed: {resp.text}")
        except Exception as e:
            # 若呼叫 API 失敗，記錄錯誤
            print(f"[Prosumer.disconnect] Failed to unsubscribe via Broker API: {e}")

    @text_decorator(role="user")
    async def receive(self, text_data=None, bytes_data=None):
        """
        收到前端訊息（JSON 格式）：
          1. 根據 event_type 做不同處理：
             - "test" => 直接呼叫 self.broker_message() 回傳前端。
             - 其他 => 可能要呼叫外部 API / 記錄 / 再由 broker.publish() 廣播給其他 Prosumer 等。
        """
        if not text_data:
            return

        data = json.loads(text_data)
        event_type = data.get("event_type", "")
        conversation_uid = data.get("conversation_uid", "")
        text_body = data.get("text", {})
        print(f"[Prosumer.receive] event_type: {event_type}, conversation_uid: {conversation_uid}, text_body: {text_body}")
        if event_type == "test":
            # 直接回應前端相同的內容
            await self.broker_message({
                "type": "broker_message",
                "event_type": "test",
                "conversation_uid": conversation_uid,
                "payload": {"text": text_body}
            })
        elif event_type == "demo":
            """
            完全依賴 text_content[0].content 來判斷第一階段/第二階段
            若 content_str == "Update SMO Info" => 第二階段
            否則 => 第一階段
            """
            text_content_list = text_body.get("text_content", [])
            first_item = text_content_list[0] if text_content_list else {}
            content_str = first_item.get("content", "")

            if content_str == "Query Field Info":
                print("=== Trigger Second Stage: UpdateSMOFlow (Mock) ===")
                
                # (a) 呼叫 LLM => 第一段
                system_prompt_2 = f"你是一個專家 AI，請簡短說明我們將要{content_str}資訊，場景應用在5G SMO當中。"
                user_msg_2 = "請描述 Query Field Info 的意義。"
                try:
                    llm_text_second = await call_openai(system_prompt_2, user_msg_2)
                except Exception as e:
                    print(f"[Demo Second-phase LLM error] {e}")
                    llm_text_second = "（LLM呼叫失敗）"

                # 傳送第一段 LLM 文字
                await self.demo_broker_message(
                    conversation_uid,
                    [{"type": "text", "content": llm_text_second}]
                )

                # (b) 執行 Mock UpdateSMOFlow => 拿回 table_data
                table_data = await second_stage_update_smo_flow(conversation_uid)

                # 傳送第二段 (table)
                await self.demo_broker_message(
                    conversation_uid,
                    [{"type": "table", "content": table_data}]
                )

            else:
                # ------------ 第一階段 ------------
                print("=== Trigger First Stage ===")

                # (A) 先呼叫 API => 取得可用場景清單
                try:
                    resp = await json_request_async(
                        module="metadata_mgt",
                        actor="ScenarioManager",
                        function="get_scenario_list",
                        method="POST",
                        payload={}
                    )
                    scenario_data_list = resp.json().get("data", [])
                except Exception as e:
                    print(f"[Demo First-phase scenario list error] {e}")
                    scenario_data_list = []

                # (B) 呼叫 LLM => 產生第一段文字
                scenario_names = [s.get("scenario_name") for s in scenario_data_list if s.get("scenario_name")]
                scenario_str = "\n".join(f"- {nm}" for nm in scenario_names) or "（沒有可用場景）"

                system_prompt_1 = "你是一個非常禮貌的AI，請向使用者介紹以下後端取得的Scenario清單："
                user_msg_1 = f"Scenario清單：\n{scenario_str}\n請幫我產生一段介紹文字。"

                try:
                    llm_text_first = await call_openai(system_prompt_1, user_msg_1)
                except Exception as e:
                    print(f"[Demo First-phase LLM error] {e}")
                    llm_text_first = "（LLM呼叫失敗）"

                # 傳送第一段 (LLM文字)
                await self.demo_broker_message(
                    conversation_uid,
                    [{"type": "text", "content": llm_text_first}]
                )

                # (C) 轉成選項 => 第二段
                choices = []
                for sc in scenario_data_list:
                    sname = sc.get("scenario_name")
                    suid = sc.get("scenario_uid")
                    if sname:
                        choices.append({"id": suid or "N/A", "label": sname})

                if not choices:
                    choices = [
                        {"id": "001", "label": "xxx_scenario"},
                        {"id": "002", "label": "yyy_scenario"}
                    ]

                await self.demo_broker_message(
                    conversation_uid,
                    [{
                        "type": "option",
                        "content": {
                            "choices": choices
                        }
                    }]
                )


        else:
            # 其他狀況下，可能需要呼叫外部 API 或 publish 給同一 conversation 的其他 Prosumer
            payload = {
                "conversation_uid": self.conversation_uid,
                "text": text_body
            }
            try:
                # 使用 json_request_async 呼叫 workflow_mgt 的 "execute_workflow"
                resp = await json_request_async(
                    module="workflow_mgt",
                    actor="WorkflowManager",
                    function="execute_workflow", 
                    method="POST",
                    payload=payload,
                )

                resp_data = resp.json()
                print(resp_data)
                text_body = resp_data.get("text", {})

                await self.broker_message({
                    "type": "broker_message",
                    "event_type": resp_data["event_type"],
                    "conversation_uid": resp_data["conversation_uid"],
                    "payload": {"text": text_body}
                })

            except Exception as e:
                # 錯誤處理
                print(f"[Prosumer] Failed to call execute workflow API: {e}")

    @text_decorator(role="llm")
    async def broker_message(self, event):
        """
        當 Broker 用 channel_layer.group_send(type="broker_message") 廣播時，會呼叫此方法。
        Prosumer 收到後，將 payload 轉給前端 WebSocket。
        """
        event_type = event["event_type"]
        conversation_uid = event["conversation_uid"]
        payload = event["payload"]
        text = payload.get("text", "")
        await self.send(text_data=json.dumps({
            "event_type": event_type,
            "conversation_uid": conversation_uid,
            "text": text
        }, ensure_ascii=False))


    async def demo_broker_message(self, conversation_uid: str, text_content_list: list):
        """
        統一格式回傳 event_type = "demo"
        text_content_list: e.g. [
          { "type": "text",  "content": "some text" },
          { "type": "table", "content": {"headers": [...], "rows": [...]} },
          { "type": "option", "content": {"choices": [...]} }
        ]
        """
        message = {
            "event_type": "demo",
            "conversation_uid": conversation_uid,
            "text": {
                "text_content": text_content_list
            }
        }
        await self.send(text_data=json.dumps(message, ensure_ascii=False))


async def second_stage_update_smo_flow(conversation_uid: str) -> dict:
    """
    模擬 "UpdateSMOFlow" 的第二階段流程，
    以您提供的真實 API 回應作為執行結果。

    執行步驟 (假裝呼叫三支 API):
      1) login => 取得 session_id
      2) queryFieldInfo => 取得查詢資料
      3) filterData => 取得最終結果

    最後整理出 table_data (headers, rows)，
    回傳給呼叫端在前端顯示。
    """

    # ----------------------------------------------------
    # 以下三段為「真實回傳內容」的文字，非真的 requests 呼叫
    # ----------------------------------------------------
    # (1) Login 的結果
    print("=== 登入 ===")
    print("狀態碼: 200")
    print("回傳內容: {'role': 2, 'session': 'irm_session_389a522a', 'showExpireAlarm': False}")
    print("取得的 session_id: irm_session_389a522a")
    session_id = "irm_session_389a522a"  # 從上面取出

    # (2) queryFieldInfo 的結果
    print("\n=== queryFieldInfo ===")
    print("狀態碼: 200")
    query_info = {
        "id": "745f7b37d5ad4876bc19",
        "name": "f1",
        "phone": "0900000000",
        "coverage": "100",
        "alarmCriticalNum": 5,
        "alarmMajorNum": 7228,
        "alarmMinorNum": 1661,
        "alarmWarningNum": 0
        # 此處只列出較關鍵的欄位
    }
    print("回傳內容:", query_info)

    # (3) filterData 的結果
    print("\n=== filterData ===")
    print("狀態碼: 200")
    filter_result = {
        "result_type": "text",
        "result_payload": {"name": "f1"}
    }
    print("回傳內容:", filter_result)

    # ------------------------------------
    # 將上述「真實內容」組合成您需要的 Table
    # ------------------------------------
    table_headers = [
        "Session ID",
        "Field ID",
        "Field Name",
        "Phone",
        "Coverage",
        "Major Alarm",
        "Minor Alarm",
        "Filter Name"
    ]

    # 從第三支API中取得的「filterData」看起來只包含名字 "f1"
    # 這裡把三支結果合併整理成一筆 row
    row_session_id = session_id
    row_field_id = query_info.get("id", "")
    row_field_name = query_info.get("name", "")
    row_phone = query_info.get("phone", "")
    row_coverage = query_info.get("coverage", "")
    row_major_alarm = query_info.get("alarmMajorNum", "")
    row_minor_alarm = query_info.get("alarmMinorNum", "")

    # 第三支 API (filterData) 的 result_payload 裏面有 "name": "f1"
    row_filter_name = filter_result.get("result_payload", {}).get("name", "")

    table_rows = [[
        row_session_id,
        row_field_id,
        row_field_name,
        row_phone,
        row_coverage,
        row_major_alarm,
        row_minor_alarm,
        row_filter_name
    ]]

    table_data = {
        "headers": table_headers,
        "rows": table_rows
    }

    # 您可以視需要再印出結果給後端除錯
    print("\n=== Final Table for UpdateSMOFlow ===")
    print(table_data)

    return table_data