import json
from channels.generic.websocket import AsyncWebsocketConsumer

from main.utils.TextDecorator import text_decorator
from main.utils.ApiKit import json_request_async
from main.utils.logger import async_log_writer

class Prosumer(AsyncWebsocketConsumer):
    """
    Prosumer：
      - 在 connect() 時向 Broker 訂閱 (conversation_uid)，若找不到該 Topic 則關閉連線。
      - 在 disconnect() 時向 Broker 取消訂閱。
      - 在 receive() 中接收前端訊息，依據 event_type 決定要如何處理（如直接回傳或呼叫外部 API）。
      - 在 broker_message() 中處理 Broker 廣播的訊息並回傳給前端。
    """

    async def connect(self):
        try:
            self.conversation_uid = self.scope["url_route"]["kwargs"].get("conversation_uid")
            self.group_name = f"conv_{self.conversation_uid}"

            # 1) 驗證 conversation 是否存在 (略) ...
            #    如果不存在 => await self.close(code=400)

            # 2) 向 Broker 訂閱 (略) ...
            #    如果訂閱失敗 => await self.close(code=400)

            # 3) 加入 Django Channels 群組
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()

            await async_log_writer(
                log_level="INFO",
                status_code="201",
                source_type="Websocket",
                func=self.connect,
                args=[self],
                message="WebSocket connect success"
            )

        except Exception as e:
            await async_log_writer(
                log_level="ERROR",
                status_code="500",
                source_type="Websocket",
                func=self.connect,
                args=[self],
                message=f"WebSocket connect Error: {str(e)}"
            )

    async def disconnect(self, code):
        # 取消訂閱 Broker (略)
        # 離開 Django Channels 群組
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        await async_log_writer(
            log_level="INFO",
            status_code="200",
            source_type="Websocket",
            func=self.disconnect,
            args=[self],
            message="WebSocket disconnect success"
        )

    @text_decorator()
    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        data = json.loads(text_data)
        event_type = data.get("event_type", "")
        conversation_uid = data.get("conversation_uid", "")
        text_body = data.get("text", {})

        if event_type == "test":
            # test: 只回傳給當前這條連線 (單點)
            await self.send(text_data=json.dumps({
                "event_type": "test",
                "conversation_uid": conversation_uid,
                "text": text_body
            }, ensure_ascii=False))

        elif event_type == "demo":
            # demo: 呼叫 workflow 後，將結果「廣播」給同群組的所有連線
            try:
                payload = {
                    "conversation_uid": self.conversation_uid,
                    "text": text_body
                }
                resp = await json_request_async(
                    module="workflow_mgt",
                    actor="WorkflowManager",
                    function="execute_workflow", 
                    method="POST",
                    payload=payload,
                )
                resp_data = resp.json()
                text = resp_data.get("text", "小廢物")

                # 這裡把要廣播的結果塞入 text_body
                # payload = {
                #     "event_type": "demo",
                #     "conversation_uid": self.conversation_uid,
                #     "text":{
                #         "text_content": [
                #             {
                #                 "type":"message",
                #                 "content": text
                #             }
                #         ]
                #     }
                # }

                # # **重點：使用 group_send 廣播給 group_name 裡的所有 Consumer**
                # await self.group_send(payload)

                await async_log_writer(
                    log_level="INFO",
                    status_code="200",
                    source_type="Websocket",
                    func=self.receive,
                    args=[self],
                    message="WebSocket receive success"
                )

            except Exception as e:
                print(f"[Prosumer] Failed to call execute_workflow API: {e}")
                await async_log_writer(
                    log_level="INFO",
                    status_code="200",
                    source_type="Websocket",
                    func=self.receive,
                    args=[self],
                    message=f"WebSocket failed to call execute_workflow API: {e}"
                )


    async def group_send(self,payload):
        await self.channel_layer.group_send(
                    self.group_name,
                    {
                        "type": "broker_message",  
                        "event_type": payload["event_type"],
                        "conversation_uid": payload["conversation_uid"],
                        "payload": {"text": payload["text"]}
                    }
                )    
        await async_log_writer(
            log_level="INFO",
            status_code="200",
            source_type="Websocket",
            func=self.group_send,
            args=[self],
            message="WebSocket group_send success"
        )

    @text_decorator()
    async def broker_message(self, event):
        """
        當 channel_layer.group_send(type="broker_message") 被呼叫時，
        就會觸發同一群組內每個 Prosumer 的 broker_message()。
        這裡再把 event payload 寫回各自的 WebSocket。
        """
        event_type = event["event_type"]
        conversation_uid = event["conversation_uid"]
        payload = event["payload"]
        text_body = payload.get("text", {})

        # 這裡就是「把同一條消息 broadcast 到每個連線」的原理，
        # 每個 Prosumer 都會執行自己的 send(...)。
        await self.send(text_data=json.dumps({
            "event_type": event_type,
            "conversation_uid": conversation_uid,
            "text": text_body
        }, ensure_ascii=False))

        await async_log_writer(
            log_level="INFO",
            status_code="200",
            source_type="Websocket",
            func=self.broker_message,
            args=[self],
            message="WebSocket broker_message success"
        )
