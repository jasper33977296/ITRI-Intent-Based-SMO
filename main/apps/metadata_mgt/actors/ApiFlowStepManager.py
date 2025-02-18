# main/apps/metadata_mgt/actors/ApiFlowStepManager.py

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from main.utils.logger import log_trigger
import json

from main.apps.metadata_mgt.models.ApiFlowStepModel import ApiFlowStep
from main.apps.metadata_mgt.models.ApiFlowModel import ApiFlow

class ApiFlowStepManager:
    """
    提供 ApiFlowStep (api_flow_step) 的 CRUD API
    """

    @staticmethod
    @csrf_exempt
    @log_trigger("INFO")
    @require_http_methods(["POST"])
    def create_api_flow_step(request):
        """
        Input (POST JSON):
            {
                "api_flow_step_name": <string> [必填],
                "api_flow_step_description": <string> [選填],
                "endpoint": <string> [選填],
                "method": <string> [選填],
                "field": <json> [選填],
                "f_api_flow_uid": <string> [必填]
            }
        """
        try:
            payload = json.loads(request.body)

            required_fields = ["api_flow_step_name", "f_api_flow_uid"]
            missing = [f for f in required_fields if f not in payload]
            if missing:
                return JsonResponse({
                    "status_code": 400,
                    "status": False,
                    "message": f"缺少必填欄位: {', '.join(missing)}"
                }, status=400)

            # 確認 ApiFlow 是否存在
            flow = ApiFlow.objects.filter(api_flow_uid=payload["f_api_flow_uid"]).first()
            if not flow:
                return JsonResponse({
                    "status_code": 404,
                    "status": False,
                    "message": "ApiFlow not found"
                }, status=404)

            step = ApiFlowStep.objects.create(
                api_flow_step_name=payload["api_flow_step_name"],
                api_flow_step_description=payload.get("api_flow_step_description", ""),
                endpoint=payload.get("endpoint", ""),
                method=payload.get("method", ""),
                field=payload.get("field", None),
                f_api_flow_uid=flow
            )

            return JsonResponse({
                "status_code": 200,
                "status": True,
                "message": "ApiFlowStep created successfully.",
                "data": {
                    "api_flow_step_uid": str(step.api_flow_step_uid),
                    "api_flow_step_name": step.api_flow_step_name
                }
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({
                "status_code": 400,
                "status": False,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "status": False,
                "message": f"系統發生錯誤: {str(e)}"
            }, status=500)

    @staticmethod
    @csrf_exempt
    @log_trigger("INFO")
    @require_http_methods(["POST"])
    def get_api_flow_step_list(request):
        """
        Input (POST JSON):
            {
                "f_api_flow_uid": <string> (選填，若提供則只查該Flow底下)
            }
        """
        try:
            payload = json.loads(request.body)
            flow_uid = payload.get("f_api_flow_uid")

            if flow_uid:
                steps = ApiFlowStep.objects.filter(f_api_flow_uid__api_flow_uid=flow_uid).order_by('-created_at')
            else:
                steps = ApiFlowStep.objects.all().order_by('-created_at')

            data = []
            for step in steps:
                data.append({
                    "api_flow_step_uid": str(step.api_flow_step_uid),
                    "api_flow_step_name": step.api_flow_step_name,
                    "api_flow_step_description": step.api_flow_step_description,
                    "endpoint": step.endpoint,
                    "method": step.method,
                    "field": step.field,
                    "api_flow_uid": str(step.f_api_flow_uid.api_flow_uid)
                })

            return JsonResponse({
                "status_code": 200,
                "status": True,
                "message": "Success",
                "data": data
            }, status=200)

        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "status": False,
                "message": f"系統發生錯誤: {str(e)}"
            }, status=500)

    @staticmethod
    @csrf_exempt
    @log_trigger("INFO")
    @require_http_methods(["POST"])
    def get_api_flow_step(request):
        """
        Input (POST JSON):
            {
                "api_flow_step_uid": <string> [必填]
            }
        """
        try:
            payload = json.loads(request.body)
            if "api_flow_step_uid" not in payload:
                return JsonResponse({
                    "status_code": 400,
                    "status": False,
                    "message": "缺少 api_flow_step_uid"
                }, status=400)

            step = ApiFlowStep.objects.filter(api_flow_step_uid=payload["api_flow_step_uid"]).first()
            if not step:
                return JsonResponse({
                    "status_code": 404,
                    "status": False,
                    "message": "ApiFlowStep not found"
                }, status=404)

            return JsonResponse({
                "status_code": 200,
                "status": True,
                "message": "Success",
                "data": {
                    "api_flow_step_uid": str(step.api_flow_step_uid),
                    "api_flow_step_name": step.api_flow_step_name,
                    "api_flow_step_description": step.api_flow_step_description,
                    "endpoint": step.endpoint,
                    "method": step.method,
                    "field": step.field,
                    "api_flow_uid": str(step.f_api_flow_uid.api_flow_uid),
                    "created_at": step.created_at,
                    "updated_at": step.updated_at
                }
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({
                "status_code": 400,
                "status": False,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "status": False,
                "message": f"系統發生錯誤: {str(e)}"
            }, status=500)

    @staticmethod
    @csrf_exempt
    @log_trigger("INFO")
    @require_http_methods(["POST"])
    def update_api_flow_step(request):
        """
        Input (POST JSON):
            {
                "api_flow_step_uid": <string> [必填],
                "api_flow_step_name": <string> [必填],
                "api_flow_step_description": <string> [選填],
                "endpoint": <string> [選填],
                "method": <string> [選填],
                "field": <json> [選填]
            }
        """
        try:
            payload = json.loads(request.body)

            if "api_flow_step_uid" not in payload or "api_flow_step_name" not in payload:
                return JsonResponse({
                    "status_code": 400,
                    "status": False,
                    "message": "缺少必填欄位: api_flow_step_uid, api_flow_step_name"
                }, status=400)

            step = ApiFlowStep.objects.filter(api_flow_step_uid=payload["api_flow_step_uid"]).first()
            if not step:
                return JsonResponse({
                    "status_code": 404,
                    "status": False,
                    "message": "ApiFlowStep not found"
                }, status=404)

            step.api_flow_step_name = payload["api_flow_step_name"]
            step.api_flow_step_description = payload.get("api_flow_step_description", "")
            step.endpoint = payload.get("endpoint", "")
            step.method = payload.get("method", "")
            step.field = payload.get("field", None)
            step.save()

            return JsonResponse({
                "status_code": 200,
                "status": True,
                "message": "ApiFlowStep updated successfully."
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({
                "status_code": 400,
                "status": False,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "status": False,
                "message": f"系統發生錯誤: {str(e)}"
            }, status=500)

    @staticmethod
    @csrf_exempt
    @log_trigger("INFO")
    @require_http_methods(["POST"])
    def delete_api_flow_step(request):
        """
        Input (POST JSON):
            {
                "api_flow_step_uid": <string> [必填]
            }
        """
        try:
            payload = json.loads(request.body)
            if "api_flow_step_uid" not in payload:
                return JsonResponse({
                    "status_code": 400,
                    "status": False,
                    "message": "缺少 api_flow_step_uid"
                }, status=400)

            step = ApiFlowStep.objects.filter(api_flow_step_uid=payload["api_flow_step_uid"]).first()
            if not step:
                return JsonResponse({
                    "status_code": 404,
                    "status": False,
                    "message": "ApiFlowStep not found"
                }, status=404)

            step.delete()
            return JsonResponse({
                "status_code": 200,
                "status": True,
                "message": "ApiFlowStep deleted successfully."
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({
                "status_code": 400,
                "status": False,
                "message": "無效的 JSON 格式"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "status": False,
                "message": f"系統發生錯誤: {str(e)}"
            }, status=500)
