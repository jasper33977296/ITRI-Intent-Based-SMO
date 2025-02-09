import redis
from django.conf import settings
from channels.layers import get_channel_layer

class TopicBroker:
    """
    TopicBroker 負責：
    1. 維護 conversation_uid 與 group_name 的訂閱關係（使用 Redis Set）。
    2. 使用 Django Channels 的 channel_layer.group_send 廣播訊息給所有訂閱該 conversation_uid 的組。
    """

    def __init__(self):
        # 可視需求將連線部分封裝或加上例外處理
        self._redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            username=settings.REDIS_USER,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB
        )

    def _topic_key(self, conversation_uid: str) -> str:
        """
        產生 Redis 中使用的 key，例如 "conversation:<conversation_uid>"
        """
        return f"conversation:{conversation_uid}"

    def init_topic(self, conversation_uid: str) -> None:
        """
        初始化/註冊一個對應 conversation_uid 的 Set。若已存在則不重複處理。
        預設加入一個特殊值 "__INIT__" 以表示已初始化。
        """
        key = self._topic_key(conversation_uid)
        self._redis.sadd(key, "__INIT__")

    def subscribe(self, conversation_uid: str, group_name: str) -> None:
        """
        將 group_name 加入指定 conversation_uid 的訂閱清單（Redis Set）。
        """
        key = self._topic_key(conversation_uid)
        self._redis.sadd(key, group_name)

    def unsubscribe(self, conversation_uid: str, group_name: str) -> None:
        """
        將 group_name 從指定 conversation_uid 的訂閱清單中移除。
        """
        key = self._topic_key(conversation_uid)
        self._redis.srem(key, group_name)

    def get_subscribers(self, conversation_uid: str) -> set[str]:
        """
        取得對應 conversation_uid 的所有訂閱者 group_name。
        Redis 傳回的原始資料是 bytes，需要 decode。
        """
        key = self._topic_key(conversation_uid)
        subscriber_bytes_set = self._redis.smembers(key)
        return {sub.decode("utf-8") for sub in subscriber_bytes_set}

    def topic_exists(self, conversation_uid: str) -> bool:
        """
        檢查 Redis 是否存在對應 conversation_uid 的 key。
        若要判斷「至少要有一名訂閱者」，可改為檢查 smembers() or scard() > 0。
        """
        key = self._topic_key(conversation_uid)
        return self._redis.exists(key) == 1

    async def publish(self, conversation_uid: str, event_type: str, payload: dict) -> None:
        """
        透過 Django Channels 的 group_send，將事件廣播給所有訂閱該 conversation_uid 的組。

        :param conversation_uid: 話題 (Topic) 的唯一識別
        :param event_type: 事件類型 (用於 Prosumer 端的邏輯判斷)
        :param payload: 傳遞的資料內容 (dict)
        """
        channel_layer = get_channel_layer()
        subscribers = self.get_subscribers(conversation_uid)

        for group_name in subscribers:
            await channel_layer.group_send(
                group_name,
                {
                    "type": "broker_message",  # Prosumer 端 handler: broker_message()
                    "event_type": event_type,
                    "payload": payload
                }
            )
