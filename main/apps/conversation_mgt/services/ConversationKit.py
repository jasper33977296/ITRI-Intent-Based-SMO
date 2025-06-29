import os
import json
import openai
import google.generativeai as genai
from typing import Callable

# --- Gemini API 呼叫函式  ---
def call_gemini_api_for_title(prompt: str, model_name: str = "gemini-1.5-flash") -> str:
    """僅用於生成標題的 Gemini API 呼叫。"""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key: raise ValueError("未設定 GOOGLE_API_KEY 環境變數")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        # 直接生成內容，不需對話歷史
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"[Gemini API 錯誤]: {e}")
        return "標題生成失敗"

def generate_conversation_title(
    user_prompt: str,
    api_backend: Callable[[str, str], str] = call_gemini_api_for_title,
    model_name: str = "gemini-2.5-flash"
) -> str:
    """
    根據使用者提問，呼叫指定的 API 後端來生成對話標題。
    此版本要求 LLM 輸出 JSON 格式，並在後端進行解析，以提高穩定性。

    Args:
        user_prompt (str): 使用者的原始提問。
        api_backend (Callable[[str, str], str]): 要使用的 API 函式。
        model_name (str): 要使用的模型名稱。

    Returns:
        str: 清理過的對話標題。
    """

    # 建立一個專門用於生成標題的提示 (Prompt)，要求以 JSON 格式輸出
    title_generation_prompt = f"""
### 角色 ###
你是一個標題生成器。請根據使用者輸入，產生一個簡潔、準確的中文標題。

### 任務說明 ###
1. 閱讀使用者輸入。
2. 生成一個 5 到 10 個字的中文標題。
3. 將生成的標題封裝在一個 JSON 物件中。

### 輸出格式 ###
你必須嚴格按照以下 JSON 格式輸出，不要包含任何其他文字、說明或 Markdown 語法。
{{
  "title": "這裡放生成的標題"
}}

### 使用者輸入 ###
{user_prompt}
"""
    
    # 呼叫 API 來生成標題
    raw_output = api_backend(title_generation_prompt, model_name)
    
    # 嘗試解析 JSON 並提取結果
    try:
        # 許多模型喜歡用 ```json ... ``` 包圍 JSON，我們先把它去掉
        if '```json' in raw_output:
            clean_json_str = raw_output.split('```json')[1].split('```')[0].strip()
        else:
            # 有時 JSON 被夾在文字中間，我們直接找到 `{` 和 `}`
            start = raw_output.find('{')
            end = raw_output.rfind('}') + 1
            if start != -1 and end != 0:
                 clean_json_str = raw_output[start:end]
            else:
                 # 假設整個輸出就是 JSON
                 clean_json_str = raw_output

        # 解析 JSON
        data = json.loads(clean_json_str)
        title = data['title']
        
        # 回傳最終清理過的標題
        return title.strip()

    except (json.JSONDecodeError, KeyError, IndexError) as e:
        # 如果 JSON 解析失敗 (例如模型沒有遵循指示，直接回傳純文字)
        # 我們就啟用備用方案：直接清理原始輸出文字
        print(f"JSON 解析失敗 ({e})，啟用備用清理方案。")
        # 移除常見的引號和 Markdown
        return raw_output.strip().replace("「", "").replace("」", "").replace('"', "").replace("`", "")
