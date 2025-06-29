from channels.generic.websocket import AsyncConsumer
from main.utils.ApiKit import  json_request
from main.utils.logger import async_log_writer

class Consumer(AsyncConsumer):
    async def send_message(self, event):
        """
        Broker 透過 channel_layer.group_send(type='send_message') 觸發此方法。

        流程：
        1. 檢查 payload 必填欄位：conversation_uid / text_content
        2. 呼叫 WorkflowManager.execute_workflow
        """

        # (1) 檢查必填欄位
        payload = event.get("payload", {})
        required_fields = ["conversation_uid", "text_content"]
        missing_fields = [f for f in required_fields if f not in payload]
        if missing_fields:
            await self.send_json({
				"status_code": 400,
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            })
            return

        # (2) 呼叫 WorkflowManager.execute_workflow
        conversation_uid = payload["conversation_uid"]
        text_content = payload["text_content"]
        workflow_payload = {"conversation_uid": conversation_uid, "text_content": text_content}
        json_request(
            module="workflow_mgt",
            actor="WorkflowManager",
            function="execute_workflow",
            payload=workflow_payload,
        )

        await async_log_writer(
            log_level="INFO",
            status_code="200",
            source_type="Websocket",
            func=self.send_message,
            args=[self],
            message="WebSocket send_message success"
        )

        return
