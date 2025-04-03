import json
from functools import wraps
from main.utils.ApiKit import json_request_async

def text_decorator():
    """
    建立 text 的裝飾器，可依據接收到的 event_type
    (在 receive 方法中) 動態判斷角色 ("user"/"llm")。
    適用於 Channels 的 AsyncWebsocketConsumer 方法。
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            """
            self: Prosumer 或任意 AsyncWebsocketConsumer。
            - self.conversation_uid: 連線時取得的對話 ID
            - receive(text_data=...): 前端傳來的 JSON 字串
            - broker_message(event=...): broker 廣播的事件
            """
            conversation_uid = getattr(self, "conversation_uid", None)
            # 若無 conversation_uid，不做任何事或自行處理
            if not conversation_uid:
                return await func(self, *args, **kwargs)

            text_dict = None
            role = None  # 先預設為 None，後面動態判斷

            # ---- 依照方法名稱，做對應的處理 ----
            if func.__name__ == "receive":
                # 前端透過 WebSocket .send(JSON)，對應到 self.receive(text_data=...)
                text_data = kwargs.get("text_data")
                if text_data is None and len(args) > 0:
                    text_data = args[0]  # 第 0 個位置參數
                
                if text_data:
                    try:
                        data = json.loads(text_data)
                        event_type = data.get("event_type", "")

                        # 依據 event_type 決定角色
                        if event_type == "demo":
                            role = "user"
                        else:
                            role = "llm"

                        # 解析 text_dict
                        text_dict = data.get("text", {})
                    except Exception:
                        pass  # 忽略 JSON 解析失敗

            elif func.__name__ == "broker_message":
                # broker_message(event=...)，event = { "payload": { "text": ... } }
                event = kwargs.get("event")
                if event is None and len(args) > 0:
                    event = args[0]
                if event:
                    payload = event.get("payload", {})
                    text_dict = payload.get("text", {})
                # 這邊可以自行決定固定角色，或根據需求再做判斷
                role = "llm"  

            # ---- 若有取得 text_dict，嘗試取得 text_content 並呼叫後端 API ----
            if isinstance(text_dict, dict):
                text_content = text_dict.get("text_content", None)
                if text_content is not None and role is not None:
                    create_payload = {
                        "conversation_uid": conversation_uid,
                        "text_content": text_content,
                        "role": role
                    }
                    try:
                        resp = await json_request_async(
                            module="conversation_mgt",
                            actor="TextManager",
                            function="create_text",
                            payload=create_payload
                        )
                        # 可根據需要查看 resp
                    except Exception as e:
                        print(f"[text_decorator] Failed to create text via API: {e}")

            # ---- 最後仍要執行原方法 ----
            return await func(self, *args, **kwargs)
        return wrapper
    return decorator
