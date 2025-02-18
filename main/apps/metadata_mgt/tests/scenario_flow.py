#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

# 這個腳本示範:
#  1) create_scenario
#  2) create_api_flow
#  3) create_api_flow_step
#  4) create_field
# 可以在流程最後再呼叫 get_scenario_details 檢查是否正確

BASE_URL = "http://140.118.162.94:30000/api/v1.0"  
# 請依實際情況調整，若你的 Django 在別的 host 或 port，請修改

def run_scenario_flow():
    # 1) create_scenario
    create_scenario_url = f"{BASE_URL}/metadata_mgt/ScenarioManager/create_scenario"
    scenario_data = {
        "scenario_name": "Update SMO Info1",
        "scenario_description": "更新 SMO 裝置資訊"
    }
    print("=== 1) Create Scenario ===")
    resp = requests.post(create_scenario_url, json=scenario_data)
    print("  Status:", resp.status_code)
    print("  Response:", resp.text)
    resp_json = resp.json()
    if resp.status_code != 200 or not resp_json.get("status"):
        print("  [ERROR] 建立 Scenario 失敗，結束流程。")
        return
    scenario_uid = resp_json["data"]["scenario_uid"]

    # 2) create_api_flow
    create_flow_url = f"{BASE_URL}/metadata_mgt/ApiFlowManager/create_api_flow"
    flow_data = {
        "api_flow_name": "Create SMO Monitor",
        "api_flow_description": "創建 SMO Monitor",
        "f_scenario_uid": scenario_uid
    }
    print("\n=== 2) Create ApiFlow ===")
    resp = requests.post(create_flow_url, json=flow_data)
    print("  Status:", resp.status_code)
    print("  Response:", resp.text)
    resp_json = resp.json()
    if resp.status_code != 200 or not resp_json.get("status"):
        print("  [ERROR] 建立 ApiFlow 失敗，結束流程。")
        return
    api_flow_uid = resp_json["data"]["api_flow_uid"]

    # 3) create_api_flow_step
    create_step_url = f"{BASE_URL}/metadata_mgt/ApiFlowStepManager/create_api_flow_step"
    step_data = {
        "api_flow_step_name": "Check SMO Status API",
        "api_flow_step_description": "檢查 SMO 狀態 API",
        "endpoint": "http://140.118.2.52:3000",
        "method": "POST",
        "field": ["key1", "key2"],
        "f_api_flow_uid": api_flow_uid
    }
    print("\n=== 3) Create ApiFlowStep ===")
    resp = requests.post(create_step_url, json=step_data)
    print("  Status:", resp.status_code)
    print("  Response:", resp.text)
    resp_json = resp.json()
    if resp.status_code != 200 or not resp_json.get("status"):
        print("  [ERROR] 建立 ApiFlowStep 失敗，結束流程。")
        return
    api_flow_step_uid = resp_json["data"]["api_flow_step_uid"]

    # 4) create_field (存在 MongoDB)
    create_field_url = f"{BASE_URL}/metadata_mgt/FieldManager/create_field"
    field_data = {
        "field_name": "near_realtime_device_uid",
        "field_type": "string",
        "required": True,
        "allowed_values": ["GOOD", "BAD"],
        "default_value": "GOOD",
        "f_api_flow_step_uid": api_flow_step_uid
    }
    print("\n=== 4) Create Field ===")
    resp = requests.post(create_field_url, json=field_data)
    print("  Status:", resp.status_code)
    print("  Response:", resp.text)
    resp_json = resp.json()
    if resp.status_code != 200 or not resp_json.get("status"):
        print("  [ERROR] 建立 Field 失敗，結束流程。")
        return
    inserted_id = resp_json["data"]["inserted_id"]
    print("  Field ObjectId:", inserted_id)

    # (選擇性) 5) 檢查 scenario_details
    scenario_details_url = f"{BASE_URL}/metadata_mgt/ScenarioManager/get_scenario_details"
    check_data = {
        "scenario_name": "Update SMO Info"
    }
    print("\n=== 5) Check Scenario Full Details ===")
    resp = requests.post(scenario_details_url, json=check_data)
    print("  Status:", resp.status_code)
    print("  Response:", resp.text)
    resp_json = resp.json()
    if resp.status_code == 200 and resp_json.get("status"):
        flows = resp_json["data"].get("flows", [])
        print("  flows count:", len(flows))
        if flows:
            steps = flows[0].get("steps", [])
            print("  steps count:", len(steps))
            if steps:
                fields = steps[0].get("fields", [])
                print("  fields count:", len(fields))
    else:
        print("  [WARNING] 無法取得 scenario_details 或失敗")

    print("\n=== Flow Completed Successfully ===")

if __name__ == "__main__":
    run_scenario_flow()
