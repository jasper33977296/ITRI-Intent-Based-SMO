import json
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from main.utils.TextDecorator import text_decorator
from main.utils.ApiKit import json_request_async

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
        
        if event_type == "test":
            # 直接回應前端相同的內容
            await self.broker_message({
                "type": "broker_message",
                "event_type": "test",
                "conversation_uid": conversation_uid,
                "payload": {"text": text_body}
            })
        elif event_type == "demo":
            # 其他狀況下，可能需要呼叫外部 API 或 publish 給同一 conversation 的其他 Prosumer
            payload = {
                "conversation_uid": self.conversation_uid,
                "text": text_body
            }
            try:
                #使用 json_request_async 呼叫 workflow_mgt 的 "execute_workflow"
                resp = await json_request_async(
                    module="workflow_mgt",
                    actor="WorkflowManager",
                    function="execute_workflow", 
                    method="POST",
                    payload=payload,
                )

                resp_data = resp.json()
                text = resp_data.get("text", "小廢物")

                text_body = {"text_content": [{
                                "type":"message",
                                "content":text
                            }]}
 
                await self.broker_message({
                    "type": "broker_message",
                    "event_type": "text_analysis",
                    "conversation_uid": self.conversation_uid,
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
        text_body = payload.get("text", {})
        await self.send(text_data=json.dumps({
            "event_type": event_type,
            "conversation_uid": conversation_uid,
            "text": text_body
        }, ensure_ascii=False))

    