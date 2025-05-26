import redis
from django.conf import settings
from channels.layers import get_channel_layer

class Broker:
    """
    Broker 負責：
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

    def remove_topic(self, conversation_uid: str) -> None:
        """
        刪除一個對應 conversation_uid 的 Set。
        """
        key = self._topic_key(conversation_uid)
        self._redis.delete(key)

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
    
    def topic_exists(self, conversation_uid: str) -> bool:
        """
        檢查 Redis 是否存在對應 conversation_uid 的 key。
        """
        key = self._topic_key(conversation_uid)
        return self._redis.exists(key) == 1
