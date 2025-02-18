# main/apps/metadata_mgt/actors/ApiFlowManager.py

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from main.utils.logger import log_trigger
import json

from main.apps.metadata_mgt.models.ApiFlowModel import ApiFlow
from main.apps.metadata_mgt.models.ScenarioModel import Scenario

class ApiFlowManager:
    """
    提供 ApiFlow (api_flow) 的 CRUD API
    """

    @staticmethod
    @csrf_exempt
    @log_trigger("INFO")
    @require_http_methods(["POST"])
    def create_api_flow(request):
        """
        Input (POST JSON):
            {
                "api_flow_name": <string> [必填],
                "api_flow_description": <string> [選填],
                "f_scenario_uid": <string> [必填]
            }
        """
        try:
            payload = json.loads(request.body)

            if "api_flow_name" not in payload or "f_scenario_uid" not in payload:
                return JsonResponse({
                    "status_code": 400,
                    "status": False,
                    "message": "缺少必填欄位: api_flow_name, f_scenario_uid"
                }, status=400)

            # 確認 scenario 是否存在
            scenario = Scenario.objects.filter(scenario_uid=payload["f_scenario_uid"]).first()
            if not scenario:
                return JsonResponse({
                    "status_code": 404,
                    "status": False,
                    "message": "Scenario not found"
                }, status=404)

            api_flow = ApiFlow.objects.create(
                api_flow_name=payload["api_flow_name"],
                api_flow_description=payload.get("api_flow_description", ""),
                f_scenario_uid=scenario  # 這裡要指向 scenario instance
            )

            return JsonResponse({
                "status_code": 200,
                "status": True,
                "message": "ApiFlow created successfully.",
                "data": {
                    "api_flow_uid": str(api_flow.api_flow_uid),
                    "api_flow_name": api_flow.api_flow_name
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
    def get_api_flow_list(request):
        """
        Input (POST JSON):
            {
                "f_scenario_uid": <string> (選填，若提供則只查該Scenario底下)
            }
        """
        try:
            payload = json.loads(request.body)
            f_scenario_uid = payload.get("f_scenario_uid")

            if f_scenario_uid:
                flows = ApiFlow.objects.filter(f_scenario_uid__scenario_uid=f_scenario_uid).order_by('-created_at')
            else:
                flows = ApiFlow.objects.all().order_by('-created_at')

            data = []
            for flow in flows:
                data.append({
                    "api_flow_uid": str(flow.api_flow_uid),
                    "api_flow_name": flow.api_flow_name,
                    "api_flow_description": flow.api_flow_description,
                    "scenario_uid": str(flow.f_scenario_uid.scenario_uid),
                })

            return JsonResponse({
                "status_code": 200,
                "status": True,
                "message": "Success",
                "data": data
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
    def get_api_flow(request):
        """
        Input (POST JSON):
            {
                "api_flow_uid": <string> [必填]
            }
        """
        try:
            payload = json.loads(request.body)
            if "api_flow_uid" not in payload:
                return JsonResponse({
                    "status_code": 400,
                    "status": False,
                    "message": "缺少 api_flow_uid"
                }, status=400)

            flow = ApiFlow.objects.filter(api_flow_uid=payload["api_flow_uid"]).first()
            if not flow:
                return JsonResponse({
                    "status_code": 404,
                    "status": False,
                    "message": "ApiFlow not found"
                }, status=404)

            return JsonResponse({
                "status_code": 200,
                "status": True,
                "message": "Success",
                "data": {
                    "api_flow_uid": str(flow.api_flow_uid),
                    "api_flow_name": flow.api_flow_name,
                    "api_flow_description": flow.api_flow_description,
                    "scenario_uid": str(flow.f_scenario_uid.scenario_uid),
                    "created_at": flow.created_at,
                    "updated_at": flow.updated_at
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
    def update_api_flow(request):
        """
        Input (POST JSON):
            {
                "api_flow_uid": <string> [必填],
                "api_flow_name": <string> [必填],
                "api_flow_description": <string> [選填]
            }
        """
        try:
            payload = json.loads(request.body)
            if "api_flow_uid" not in payload or "api_flow_name" not in payload:
                return JsonResponse({
                    "status_code": 400,
                    "status": False,
                    "message": "缺少必填欄位: api_flow_uid, api_flow_name"
                }, status=400)

            flow = ApiFlow.objects.filter(api_flow_uid=payload["api_flow_uid"]).first()
            if not flow:
                return JsonResponse({
                    "status_code": 404,
                    "status": False,
                    "message": "ApiFlow not found"
                }, status=404)

            flow.api_flow_name = payload["api_flow_name"]
            flow.api_flow_description = payload.get("api_flow_description", "")
            flow.save()

            return JsonResponse({
                "status_code": 200,
                "status": True,
                "message": "ApiFlow updated successfully"
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
    def delete_api_flow(request):
        """
        Input (POST JSON):
            {
                "api_flow_uid": <string> [必填]
            }
        """
        try:
            payload = json.loads(request.body)
            if "api_flow_uid" not in payload:
                return JsonResponse({
                    "status_code": 400,
                    "status": False,
                    "message": "缺少 api_flow_uid"
                }, status=400)

            flow = ApiFlow.objects.filter(api_flow_uid=payload["api_flow_uid"]).first()
            if not flow:
                return JsonResponse({
                    "status_code": 404,
                    "status": False,
                    "message": "ApiFlow not found"
                }, status=404)

            flow.delete()
            return JsonResponse({
                "status_code": 200,
                "status": True,
                "message": "ApiFlow deleted successfully."
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
