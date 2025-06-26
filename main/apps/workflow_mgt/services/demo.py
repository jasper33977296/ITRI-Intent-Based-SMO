import json
from main.utils.ApiKit import json_request_async
from main.utils.TextDecorator import text_decorator
from asgiref.sync import sync_to_async
# ❶ 直接使用新版 AsyncOpenAI；不再用舊的 openai.ChatCompletion.create()
from openai import AsyncOpenAI
import os
# 假設專案中直接建立一個全域客戶端實例，或在更高層級集中管理
openai_client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "")
)

async def call_openai(system_prompt: str, user_content: str) -> str:
    """
    改用 AsyncOpenAI 客戶端，直接以 async/await 方式呼叫。
    回傳生成的文字字串 (choices[0].message.content)。
    """
    response = await openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        temperature=1,
        max_tokens=300
    )

    # 新版回傳物件為 Pydantic Model，可直接使用屬性
    return response.choices[0].message.content.strip()

async def handle_demo_event(conversation_uid: str, user_text: str) -> dict:
    """
    處理 Prosumer 中 event_type = "demo" 的相關業務邏輯：
      1. 取得 Scenario 列表
      2. 呼叫 OpenAI 取得建議
      3. 將結果回傳給呼叫端
    """
    # ============== 1. 取得 Scenario 列表 ==============
    try:
        resp = await json_request_async(
            module="metadata_mgt",
            actor="ScenarioManager",
            function="get_scenario_list",
            method="POST",
            payload={}
        )
        resp_data = resp.json()
        scenario_data_list = resp_data.get("data", [])
        # scenario_data_list 可能是類似: [ {"scenario_uid":"...", "scenario_name":"..."}, ... ]
    except Exception as e:
        raise RuntimeError(f"Failed to get scenario list: {e}")

    # ============== 2. 呼叫 OpenAI 取得建議 ==============
    try:
        scenario_names = [sc.get("scenario_name", "") for sc in scenario_data_list]
        scenario_text = "\n".join(f"- {n}" for n in scenario_names if n)

        system_prompt = (
            "你是一個非常有禮貌的AI，現在有以下Scenario列表，請用委婉的語氣向使用者介紹這些Scenario，"
            "並根據使用者的需求給一些建議。"
        )
        content_text = f"使用者說: {user_text}\n\n目前已有的Scenario有:\n{scenario_text}"

        # 呼叫上方新版的 async function
        chat_response = await call_openai(system_prompt, content_text)

    except Exception as e:
        raise RuntimeError(f"Failed to call OpenAI: {e}")

    # ============== 3. 組合回傳結果 ==============
    return {
        "scenarios": scenario_data_list,
        "chatgpt_reply": chat_response
    }
