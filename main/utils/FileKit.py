import os
import re
import csv
import json
import shutil


def create_empty_csv(file_path: str) -> None:
    """
    建立目錄(若不存在)，並在 file_path 建立一個僅含表頭 `["text_uid"]` 的空白 CSV。
    若過程失敗，拋出例外。
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["text_uid"])  # 只含標題

def append_text_uid_to_csv(csv_path: str, text_uid: str) -> None:
    """
    在 csv_path 指定的 CSV 檔案中，新增一筆 text_uid。
    若檔案不存在，需先行處理；若是空檔案則寫入表頭。
    """
    # 確保所在資料夾已存在(通常在 create_empty_csv 時就已建立)
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    file_exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["text_uid"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # 若檔案為空，需寫入表頭
        if not file_exists or os.path.getsize(csv_path) == 0:
            writer.writeheader()
        writer.writerow({"text_uid": text_uid})


def create_text_json_file(conversation_uid: str, text_uid: str, text_content: dict) -> None:
    """
    在 texts/{conversation_uid}/{text_uid}.json 建立 JSON 檔，
    並將 text_content 寫入該檔案 (確保資料夾存在)。
    """
    text_dir = os.path.join("texts", conversation_uid)
    os.makedirs(text_dir, exist_ok=True)

    text_json_path = os.path.join(text_dir, f"{text_uid}.json")
    with open(text_json_path, "w", encoding="utf-8") as jsonfile:
        json.dump(text_content, jsonfile, ensure_ascii=False, indent=2)

def read_text_uids_from_csv(csv_path: str) -> list[str]:
    """
    讀取 csv_path 指向的 CSV 檔，回傳該檔中所有的 text_uid。
    若檔案不存在，預設回傳空清單或拋出例外（可視需求自訂）。
    """
    if not os.path.exists(csv_path):
        # 這邊可依需求拋出例外或回傳空清單
        return []

    text_uids = []
    with open(csv_path, "r", encoding="utf-8", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if "text_uid" in row and row["text_uid"]:
                text_uids.append(row["text_uid"])
    return text_uids

def read_text_jsons(conversation_uid: str, text_uids: list[str]) -> list[dict]:
    """
    根據 text_uids 中的每個 text_uid, 讀取 texts/{conversation_uid}/{text_uid}.json 檔，
    並回傳一個 list，其中每筆資料包含:
        {
            "text_uid": <string>,
            "role": <string>,
            "text": [ { "type": ..., "content": ... }, ... ]
        }
    若某個 text_uid.json 不存在，預設跳過 (或可依需求改為丟例外)。
    """
    data_list = []
    for t_uid in text_uids:
        text_json_path = os.path.join("texts", conversation_uid, f"{t_uid}.json")
        if os.path.exists(text_json_path):
            with open(text_json_path, "r", encoding="utf-8") as f:
                text_data = json.load(f)
                # 假設 text_data = {"role": <string>, "text": [ { "type":..., "content":... }, ... ] }
                data_list.append({
                    "text_uid": t_uid,
                    "role": text_data.get("role", ""),
                    "text_content": text_data.get("text_content", [])
                })
        else:
            # 檔案不存在時，預設跳過 (或可改用 raise FileNotFoundError 等做更嚴謹處理)
            pass

    return data_list

def create_json_file(json_path: str, content: dict) -> None:
    """
    在指定路徑 (json_path) 建立一個 JSON 檔案，並將 content 寫入。
    若路徑中的資料夾不存在，則自動建立。
    若寫檔失敗或 content 非可序列化物件，則拋出例外。
    """
    # 確保目錄存在
    os.makedirs(os.path.dirname(json_path), exist_ok=True)

    # 將 content 寫入 JSON 檔案
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)

def create_folder(folder_path):
    os.makedirs(folder_path, exist_ok=True)

def delete_folder(folder_path: str):
    """
    刪除指定資料夾（含其子檔案與子資料夾）
    """
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)

def delete_file(file_path: str):
    """
    刪除指定檔案
    """
    if os.path.exists(file_path):
        os.remove(file_path)

def _remove_reason_json(content: str) -> str:
    """
    從字串中移除 {"reason": ...} 樣式的 JSON 物件。
    如果輸入的不是字串，則直接回傳原內容。
    """
    if not isinstance(content, str):
        return content

    # 定義要尋找的樣式 (pattern)
    pattern = re.compile(r'\s*\{\s*"reason"\s*:\s*".*?"\s*\}', re.DOTALL)
    
    # 使用 re.sub() 將匹配到的樣式替換成空字串後，再去除前後多餘的空白
    return pattern.sub('', content).strip()

def remove_reason_json(data: dict):
    """
    解析傳入的物件，並清理 text_content 中每個元素的 content 欄位，
    移除 reason JSON 字串。

    Args:
        data (dict): 包含 role 和 text_content 的物件。

    Returns:
        dict: content 欄位已被清理乾淨的物件。
    """
    if 'text_content' in data and isinstance(data['text_content'], list):
        # 遍歷 text_content 陣列中的每一個項目 (item)
        for item in data['text_content']:
            # 確保項目是一個 dict 且含有 'content' 欄位
            if isinstance(item, dict) and 'content' in item:
                # 使用輔助函式來清理 content 字串，並更新回去
                item['content'] = _remove_reason_json(item.get('content'))
    
    return data