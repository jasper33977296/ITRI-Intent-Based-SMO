from channels.generic.websocket import AsyncConsumer
from main.utils.ApiKit import  json_request

class Consumer(AsyncConsumer):
    async def send_message(self, event):
        """
        Broker 透過 channel_layer.group_send(type='send_message') 觸發此方法。

        流程：
        1. 檢查 payload 必填欄位：event_type / conversation_uid / text
        2. 分流處理
           2a. 若 event_type == 'test' → 原樣回傳 (echo)
           2b. 若 event_type == 'demo' → 呼叫 WorkflowManager.execute_workflow
        """

        # (1) 檢查必填欄位
        payload = event.get("payload", {})
        required_fields = ["event_type", "conversation_uid", "text"]
        missing_fields = [f for f in required_fields if f not in payload]
        if missing_fields:
            await self.send_json({
				"status_code": 400,
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            })
            return

        # (2) 依 event_type 分支 
        event_type = payload["event_type"]
        conversation_uid = payload["conversation_uid"]
        text = payload["text"]

        # if event_type == "test":
        #     # 2a. echo 模式
        #     await self.send_json({"echo": payload["text"]})

        # elif event_type == "demo":
        if event_type == "demo":
            # 2b. demo → WorkflowManager.execute_workflow
            workflow_payload = {"conversation_uid": conversation_uid, "text": text}
            json_request(
                module="workflow_mgt",
                actor="WorkflowManager",
                function="execute_workflow",
                payload=workflow_payload,
            )
            return
        else:
            # 非預期的 event_type
            await self.send_json({
                "status_code": 502,
                "message": f"Unsupported event_type: {event_type}"
                })
            return
