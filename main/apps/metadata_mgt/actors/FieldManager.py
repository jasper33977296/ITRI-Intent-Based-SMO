# # main/apps/metadata_mgt/actors/FieldManager.py

# import json
# from django.views.decorators.csrf import csrf_exempt
# from django.views.decorators.http import require_http_methods
# from django.http import JsonResponse
# from main.utils.logger import log_trigger
# from main.apps.metadata_mgt.services import mongo_service

# class FieldManager:
#     """
#     透過 mongo_service.py 與 MongoDB 互動，完成 field 的 CRUD。
#     這裡先示範 create_field，後續可加上其他 method。
#     """

#     @staticmethod
#     @csrf_exempt
#     @log_trigger("INFO")
#     @require_http_methods(["POST"])
#     def create_field(request):
#         """
#         Input (POST JSON):
#             {
#               "field_id": 0,
#               "field_name": "near_realtime_device_uid",
#               "field_type": "string",
#               "required": true,
#               "min_value": 0,
#               "max_value": 9999.99,
#               "allowed_values": ["GOOD", "BAD"],
#               "default_value": "RIC-MAIN-001",
#               "f_api_flow_step_uid": "7b4856bb-5bee-4553-85a5-a4d542dfb559"
#             }

#         Output (JsonResponse):
#             {
#               "status_code": 200,
#               "status": true,
#               "message": "Field created successfully.",
#               "data": {
#                 "inserted_id": "...mongo ObjectId..."
#               }
#             }
#         """
#         try:
#             payload = json.loads(request.body)

#             # 檢查必填欄位 (僅示範部份)
#             required_fields = ["field_id", "field_name", "field_type", "required", "f_api_flow_step_uid"]
#             missing = [f for f in required_fields if f not in payload]
#             if missing:
#                 return JsonResponse({
#                     "status_code": 400,
#                     "status": False,
#                     "message": f"缺少必填欄位: {', '.join(missing)}"
#                 }, status=400)

#             # 組裝要存進 MongoDB 的 document
#             document = {
#                 "field_id": payload["field_id"],
#                 "field_name": payload["field_name"],
#                 "field_type": payload["field_type"],
#                 "required": payload["required"],
#                 "allowed_values": payload.get("allowed_values", []),
#                 "default_value": payload.get("default_value"),
#                 "f_api_flow_step_uid": payload["f_api_flow_step_uid"],
#                 # 你若想紀錄 created_at / updated_at 也可以:
#                 # "created_at": datetime.now().isoformat(),
#                 # "updated_at": datetime.now().isoformat(),
#             }

#             inserted_id = mongo_service.insert_field(document)

#             return JsonResponse({
#                 "status_code": 200,
#                 "status": True,
#                 "message": "Field created successfully.",
#                 "data": {
#                     "inserted_id": inserted_id
#                 }
#             }, status=200)

#         except json.JSONDecodeError:
#             return JsonResponse({
#                 "status_code": 400,
#                 "status": False,
#                 "message": "無效的 JSON 格式"
#             }, status=400)
#         except Exception as e:
#             return JsonResponse({
#                 "status_code": 500,
#                 "status": False,
#                 "message": f"系統發生錯誤: {str(e)}"
#             }, status=500)
#     @staticmethod
#     def _check_and_update_step_ready(step_uid: str):
#         """
#         若該 step 底下所有 field 都 field_ready=True，則把 ApiFlowStep.api_flow_step_ready = True
#         否則 False。
#         """
#         # 查詢該 step 底下所有 field
#         query = {"f_api_flow_step_uid": step_uid}
#         fields = mongo_service.find_fields(query)

#         # 如果所有 field 的 field_ready 都是 True，表示這個 Step 已經 ready
#         all_ready = True
#         for doc in fields:
#             if not doc.get("field_ready", False):
#                 all_ready = False
#                 break

#         # 更新 Postgres 的 Step
#         step = ApiFlowStep.objects.filter(api_flow_step_uid=step_uid).first()
#         if step:
#             step.api_flow_step_ready = all_ready
#             step.save()