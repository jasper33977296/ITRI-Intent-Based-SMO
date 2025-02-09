import os
import json
from openai import OpenAI


def text_analysis(user_prompt):
    """
    範例：確認能與 GPT 正常溝通，
    並將結果以 Python dict 回傳給呼叫者 (通常是 WorkflowManager)。

    Params:
        user_prompt (str): 使用者輸入內容
    
    Returns:
        dict: {
            "status": bool,           # True: 成功, False: 失敗
            "message": str,           # 錯誤或說明資訊
            "parsed_data": any,       # 從 GPT 解析出的資料 (若成功)
            "raw_gpt_response": str   # GPT 原始回傳字串 (若需除錯，可選)
        }
    """
    client = OpenAI(
        api_key="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",  # This is the default and can be omitted
    )
    # System Prompt：示範如何對 GPT 設定指令，如需產生 2D array 代表先後/並行子需求等
    system_prompt = """
        你是一個能解析中文多需求(命題)的助理, 能判斷哪些需求可並行(同時).
        請用 2D陣列表示先後順序, 相同陣列表示並行.
    """

    try: 
        # 1. 呼叫 GPT
        chat_completion = client.chat.completions.create(
        messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": f"""{user_prompt}
                                                    請先列出子需求,給id(1,2,3..),再以 "order"=[ [...],[...]] 格式表示先後/並行:
                                                    如:
                                                    {{
                                                    "subneeds":[{{"id":1,"text":"查詢A"}},{{"id":2,"text":"查詢B"}},{{"id":3,"text":"檢查付款"}}],
                                                    "order":[[1,2],[3]]
                                                    }}
                 """},
            ],
            model="gpt-3.5-turbo",
        )
        
        gpt_response = chat_completion.choices[0].message.content.strip()

        return {
            "text_content":[
                {
                "type":"message",
                "content":gpt_response
                }
            ]
        }

    except json.JSONDecodeError:
        # GPT 回傳內容無法被 json.loads() 成為合法 JSON
        return {
            "status": False,
            "message": "GPT 回傳的不是有效 JSON 格式",
            "parsed_data": None,
            "raw_gpt_response": gpt_response if 'gpt_response' in locals() else None
        }

    except Exception as e:
        return {
            "status": False,
            "message": str(e),
            "parsed_data": None,
            "raw_gpt_response": None
        }