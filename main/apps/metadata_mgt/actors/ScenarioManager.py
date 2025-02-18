# main/apps/metadata_mgt/actors/ScenarioManager.py

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from main.utils.logger import log_trigger
import json

from main.apps.metadata_mgt.models.ScenarioModel import Scenario
from main.apps.metadata_mgt.services import mongo_service

class ScenarioManager:
    """
    提供 Scenario (scenario) 的 CRUD API
    """

    @staticmethod
    @csrf_exempt
    @log_trigger("INFO")
    @require_http_methods(["POST"])
    def create_scenario(request):
        """
        Input (POST JSON):
            {
                "scenario_name": <string> [必填],
                "scenario_description": <string> [選填]
            }
        """
        try:
            payload = json.loads(request.body)

            # 檢查必填欄位
            if "scenario_name" not in payload:
                return JsonResponse({
                    "status_code": 400,
                    "status": False,
                    "message": "缺少必填欄位: scenario_name"
                }, status=400)

            scenario = Scenario.objects.create(
                scenario_name=payload["scenario_name"],
                scenario_description=payload.get("scenario_description", "")
            )

            return JsonResponse({
                "status_code": 200,
                "status": True,
                "message": "Scenario created successfully.",
                "data": {
                    "scenario_uid": str(scenario.scenario_uid),
                    "scenario_name": scenario.scenario_name
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
    def get_scenario_list(request):
        """
        Input (POST JSON): {} (本例不需任何欄位，或依需求自行調整)

        Output:
            回傳 scenario 的列表
        """
        try:
            # 直接查詢全部
            scenarios = Scenario.objects.all().order_by('-created_at')
            data = []
            for sc in scenarios:
                data.append({
                    "scenario_uid": str(sc.scenario_uid),
                    "scenario_name": sc.scenario_name,
                    "scenario_description": sc.scenario_description
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
    def get_scenario(request):
        """
        Input (POST JSON):
            {
                "scenario_uid": <string> [必填]
            }
        """
        try:
            payload = json.loads(request.body)
            if "scenario_uid" not in payload:
                return JsonResponse({
                    "status_code": 400,
                    "status": False,
                    "message": "缺少 scenario_uid"
                }, status=400)

            scenario = Scenario.objects.filter(scenario_uid=payload["scenario_uid"]).first()
            if not scenario:
                return JsonResponse({
                    "status_code": 404,
                    "status": False,
                    "message": "Scenario not found"
                }, status=404)

            return JsonResponse({
                "status_code": 200,
                "status": True,
                "message": "Success",
                "data": {
                    "scenario_uid": str(scenario.scenario_uid),
                    "scenario_name": scenario.scenario_name,
                    "scenario_description": scenario.scenario_description,
                    "created_at": scenario.created_at,
                    "updated_at": scenario.updated_at
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
    def update_scenario(request):
        """
        Input (POST JSON):
            {
                "scenario_uid": <string> [必填],
                "scenario_name": <string> [必填],
                "scenario_description": <string> [選填]
            }
        """
        try:
            payload = json.loads(request.body)

            if "scenario_uid" not in payload or "scenario_name" not in payload:
                return JsonResponse({
                    "status_code": 400,
                    "status": False,
                    "message": "缺少必填欄位: scenario_uid, scenario_name"
                }, status=400)

            scenario = Scenario.objects.filter(scenario_uid=payload["scenario_uid"]).first()
            if not scenario:
                return JsonResponse({
                    "status_code": 404,
                    "status": False,
                    "message": "Scenario not found"
                }, status=404)

            scenario.scenario_name = payload["scenario_name"]
            scenario.scenario_description = payload.get("scenario_description", "")
            scenario.save()

            return JsonResponse({
                "status_code": 200,
                "status": True,
                "message": "Scenario updated successfully.",
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
    def delete_scenario(request):
        """
        Input (POST JSON):
            {
                "scenario_uid": <string> [必填]
            }
        """
        try:
            payload = json.loads(request.body)
            if "scenario_uid" not in payload:
                return JsonResponse({
                    "status_code": 400,
                    "status": False,
                    "message": "缺少 scenario_uid"
                }, status=400)

            scenario = Scenario.objects.filter(scenario_uid=payload["scenario_uid"]).first()
            if not scenario:
                return JsonResponse({
                    "status_code": 404,
                    "status": False,
                    "message": "Scenario not found"
                }, status=404)

            scenario.delete()
            return JsonResponse({
                "status_code": 200,
                "status": True,
                "message": "Scenario deleted successfully."
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
    def get_scenario_details(request):
        """
        依照 scenario_name 找出:
         - Scenario
         - ApiFlow (底下)
         - ApiFlowStep (底下)
         - Field (透過 MongoDB, 依 step uid 找)
         
        Input (POST JSON):
            {
                "scenario_name": <string> (必填)
            }
        
        Output (JsonResponse):
            {
                "status_code": 200,
                "status": true,
                "message": "Success",
                "data": {
                    "scenario_uid": "...",
                    "scenario_name": "...",
                    "scenario_description": "...",
                    "flows": [
                        {
                            "api_flow_uid": "...",
                            "api_flow_name": "...",
                            "api_flow_description": "...",
                            "created_at": "...",
                            "updated_at": "...",
                            "steps": [
                                {
                                    "api_flow_step_uid": "...",
                                    "api_flow_step_name": "...",
                                    "api_flow_step_description": "...",
                                    "endpoint": "...",
                                    "method": "...",
                                    "field": ...,
                                    "created_at": "...",
                                    "updated_at": "...",
                                    "fields": [  // 來自 Mongo
                                        {
                                            "_id": "<mongo objectId>",
                                            "field_name": "...",
                                            ...
                                        },
                                        ...
                                    ]
                                },
                                ...
                            ]
                        },
                        ...
                    ]
                }
            }
        """
        try:
            payload = json.loads(request.body)
            if "scenario_name" not in payload:
                return JsonResponse({
                    "status_code": 400,
                    "status": False,
                    "message": "缺少必填欄位: scenario_name"
                }, status=400)

            scenario_name = payload["scenario_name"]
            scenario = Scenario.objects.filter(scenario_name=scenario_name).first()
            if not scenario:
                return JsonResponse({
                    "status_code": 404,
                    "status": False,
                    "message": f"Scenario with name '{scenario_name}' not found"
                }, status=404)

            # 取得該 scenario 相關 ApiFlow (One-to-Many)
            flows = scenario.api_flows.all().order_by('created_at')

            flow_list = []
            for flow in flows:
                # 取得 flow 底下的 ApiFlowStep
                steps = flow.api_flow_steps.all().order_by('created_at')
                step_list = []
                for step in steps:
                    # 透過 f_api_flow_step_uid 在 MongoDB 的 "field" collection 中找對應
                    query = {"f_api_flow_step_uid": str(step.api_flow_step_uid)}
                    field_docs = mongo_service.find_fields(query)  # list of dict
                    # 把每個 field doc 轉成想回傳的格式
                    field_data_list = []
                    for doc in field_docs:
                        field_data_list.append({
                            "_id": str(doc.get("_id")),
                            "field_id": doc.get("field_id"),
                            "field_name": doc.get("field_name"),
                            "field_type": doc.get("field_type"),
                            "required": doc.get("required"),
                            "allowed_values": doc.get("allowed_values"),
                            "default_value": doc.get("default_value"),
                            "f_api_flow_step_uid": doc.get("f_api_flow_step_uid"),
                            # 你也可擴充 doc 其他欄位( created_at, updated_at ), depends on your doc
                        })

                    step_list.append({
                        "api_flow_step_uid": str(step.api_flow_step_uid),
                        "api_flow_step_name": step.api_flow_step_name,
                        "api_flow_step_description": step.api_flow_step_description,
                        "endpoint": step.endpoint,
                        "method": step.method,
                        "field": step.field,  # 這是Postgres JSONField
                        "created_at": step.created_at,
                        "updated_at": step.updated_at,
                        "fields": field_data_list
                    })

                flow_list.append({
                    "api_flow_uid": str(flow.api_flow_uid),
                    "api_flow_name": flow.api_flow_name,
                    "api_flow_description": flow.api_flow_description,
                    "created_at": flow.created_at,
                    "updated_at": flow.updated_at,
                    "steps": step_list
                })

            # 組合整體回應
            return JsonResponse({
                "status_code": 200,
                "status": True,
                "message": "Success",
                "data": {
                    "scenario_uid": str(scenario.scenario_uid),
                    "scenario_name": scenario.scenario_name,
                    "scenario_description": scenario.scenario_description,
                    "created_at": scenario.created_at,
                    "updated_at": scenario.updated_at,
                    "flows": flow_list
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