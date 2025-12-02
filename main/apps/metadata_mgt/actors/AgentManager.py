import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from main.utils.logger import log_trigger
from main.apps.metadata_mgt.services.AgentController import AgentController
from main.utils.ApiKit import json_request


class AgentManager:
    """
    提供對 Agent Model 進行 Create / Read / Update / Delete 的方法，
    並使用 AgentController 進行業務邏輯處理。
    """

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def create_agent_metadata(request):
        """
        建立 agent metadata。
        
        Required:
            - user_uid: UUID
            - agent_name: string
            - api_key: string (optional)
        """
        try:
            payload = json.loads(request.body)

            # 必填欄位檢查
            required_fields = ["user_uid", "agent_name"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"缺少必填欄位: {', '.join(missing_fields)}"
                }, status=400)

            # 呼叫 Controller 建立
            response = AgentController.create_agent(
                user_uid=payload['user_uid'],
                agent_name=payload['agent_name'],
                api_key=payload.get('api_key')
            )

            return JsonResponse(response, status=response["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({
                "status_code": 400,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "message": f"系統發生錯誤，請稍後再試: {str(e)}"
            }, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def get_agent_name(request):
        """
        取得單一 agent 名稱。
        
        Required:
            - agent_uid: UUID
        """
        try:
            payload = json.loads(request.body)

            # 必填欄位檢查
            required_fields = ["agent_uid"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"缺少必填欄位: {', '.join(missing_fields)}"
                }, status=400)

            # 呼叫 Controller 查詢
            response = AgentController.get_agent_name(payload["agent_uid"])

            return JsonResponse(response, status=response["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({
                "status_code": 400,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "message": f"系統發生錯誤，請稍後再試: {str(e)}"
            }, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def get_agent_list_metadata(request):
        """
        取得 agent 清單 metadata。
        
        Required:
            - user_uid: UUID
        """
        try:
            payload = json.loads(request.body)

            # 必填欄位檢查
            required_fields = ["user_uid"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"缺少必填欄位: {', '.join(missing_fields)}"
                }, status=400)

            # 呼叫 Controller 查詢
            response = AgentController.get_agent_list(payload["user_uid"])

            return JsonResponse(response, status=response["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({
                "status_code": 400,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "message": f"系統發生錯誤，請稍後再試: {str(e)}"
            }, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def update_agent_metadata(request):
        """
        更新 agent metadata。
        
        Required:
            - agent_uid: UUID
        Optional:
            - agent_name: string
            - api_key: string
        """
        try:
            payload = json.loads(request.body)

            # 必填欄位檢查
            required_fields = ["agent_uid"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"缺少必填欄位: {', '.join(missing_fields)}"
                }, status=400)

            # 呼叫 Controller 更新
            response = AgentController.update_agent(
                agent_uid=payload['agent_uid'],
                agent_name=payload.get('agent_name'),
                api_key=payload.get('api_key')
            )

            return JsonResponse(response, status=response["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({
                "status_code": 400,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "message": f"系統發生錯誤，請稍後再試: {str(e)}"
            }, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def delete_agent_metadata(request):
        """
        刪除 agent metadata。
        
        Required:
            - agent_uid: UUID
        """
        try:
            payload = json.loads(request.body)

            # 必填欄位檢查
            required_fields = ["agent_uid"]
            missing_fields = [f for f in required_fields if f not in payload]
            if missing_fields:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"缺少必填欄位: {', '.join(missing_fields)}"
                }, status=400)

            # 先透過 Controller 取得 agent 詳細資料 (含 user_uid)，避免直接操作 Model
            agent_detail = AgentController.get_agent(payload["agent_uid"])
            if agent_detail.get("status_code") != 200:
                return JsonResponse(agent_detail, status=agent_detail.get("status_code", 400))

            user_uid = agent_detail["data"]["user_uid"]
            agent_uid = agent_detail["data"]["agent_uid"]

            # 呼叫 conversation_mgt 取得該 agent 的對話清單
            try:
                resp = json_request(
                    module="conversation_mgt",
                    actor="ConversationManager",
                    function="get_agent_conversation_list",
                    payload={
                        "user_uid": user_uid,
                        "agent_uid": agent_uid
                    },
                )
                conv_list_result = resp.json()
            except Exception as e:
                return JsonResponse({
                    "status_code": 502,
                    "message": f"Fail to call conversation_mgt (get_agent_conversation_list): {str(e)}"
                }, status=502)

            # 若服務回傳非 200，轉傳錯誤並中止刪除 agent
            if conv_list_result.get("status_code") != 200:
                return JsonResponse(conv_list_result, status=conv_list_result.get("status_code", 400))

            conversations = conv_list_result.get("data", []) or []

            # 逐一刪除對話，使用 conversation_mgt 的 delete_conversation，確保檔案/圖片/topic 一併清掉
            for item in conversations:
                conversation_uid = item.get("conversation_uid")
                if not conversation_uid:
                    continue
                try:
                    del_resp = json_request(
                        module="conversation_mgt",
                        actor="ConversationManager",
                        function="delete_conversation",
                        payload={"conversation_uid": conversation_uid},
                    )
                    del_result = del_resp.json()
                except Exception as e:
                    return JsonResponse({
                        "status_code": 502,
                        "message": f"Fail to call conversation_mgt (delete_conversation) for {conversation_uid}: {str(e)}"
                    }, status=502)

                if del_result.get("status_code") != 200:
                    return JsonResponse(del_result, status=del_result.get("status_code", 400))

            # 呼叫 Controller 刪除
            response = AgentController.delete_agent(payload["agent_uid"])

            return JsonResponse(response, status=response["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({
                "status_code": 400,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "message": f"系統發生錯誤，請稍後再試: {str(e)}"
            }, status=500)
