import json
from functools import wraps
from main.utils.ApiKit import json_request_async

def text_decorator(role: str):
    """
    建立 text 的裝飾器，可依據傳入的 role("user"/"llm")，
    自動組出對應的 payload，並透過非同步 json_request_async 呼叫 API。
    適用於 Channels 的 AsyncWebsocketConsumer 方法。
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            """
            self: Broker 或任意 AsyncWebsocketConsumer。
            - self.conversation_uid: 連線時取得的對話 ID
            - receive(text_data=...): 前端傳來的 JSON 字串
            - broker_message(event=...): Producer 廣播的事件
            """
            conversation_uid = getattr(self, "conversation_uid", None)
            # 若無 conversation_uid，不做任何事或自行處理
            if not conversation_uid:
                return await func(self, *args, **kwargs)

            # ---- 依照方法名稱判斷要從哪裡取得文字 ----
            
            if func.__name__ == "receive":
                # 前端透過 WebSocket .send(JSON)，對應到 self.receive(text_data=...)
                text_data = kwargs.get("text_data")
                if text_data is None and len(args) > 0:
                    text_data = args[0]  # 第0個位置參數

                if text_data:
                    try:
                        data = json.loads(text_data)
                        # receive(text_data=...)，text_data = { ..., "text_content": [...] }
                        text_content = data.get("text_content", {})
                    except Exception:
                        pass  # 忽略 JSON 解析失敗

            elif func.__name__ == "broker_message":
                # broker_message(event=...)，event = { "payload": { "text_content": ... } }
                event = kwargs.get("event")
                if event is None and len(args) > 0:
                    event = args[0]
                if event:
                    payload = event.get("payload", {})
                    text_content = payload.get("text_content", {})

            # # ---- 若取得 text_dict，嘗試取得 text_content ----
            # # 例： text_dict = { "text_content": [ { "type": "text", "content": "..." } ] }
            # if isinstance(text_dict, dict):
            #     text_content = text_dict.get("text_content", None)
            if text_content is not None:
                create_payload = {
                    "conversation_uid": conversation_uid,
                    "text_content": text_content,
                    "role": role
                }
                try:
                    # 使用您提供的 json_request_async 進行非同步 API 呼叫
                    resp = await json_request_async(
                        module="conversation_mgt",
                        actor="TextManager",
                        function="create_text",
                        payload=create_payload
                    )
                    # 根據需要，您可以檢查 resp.status_code, resp.json() 等
                    # example:
                    # result = resp.json()
                    # print("[text_decorator] Response from text_mgt:", result)
                except Exception as e:
                    print(f"[text_decorator] Failed to create text via API: {e}")

            # ---- 最後仍要執行原方法 ----
            return await func(self, *args, **kwargs)
        return wrapper
    return decorator
