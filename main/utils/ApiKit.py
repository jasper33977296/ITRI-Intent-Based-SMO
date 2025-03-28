import os
import requests
import httpx

# 先定義各個 module 與其對應的環境變數
MODULE_ENV_MAPPING = {
    'metadata_mgt': {
        'host': 'HTTP_METADATA_MGT_HOST',
        'port': 'HTTP_METADATA_MGT_PORT',
        'api_version': 'METADATA_MGT_API_VERSION',
    },
    'topic_mgt': {
        'host': 'HTTP_TOPIC_MGT_HOST',
        'port': 'HTTP_TOPIC_MGT_PORT',
        'api_version': 'TOPIC_MGT_API_VERSION',
    },
    'workflow_mgt': {
        'host': 'HTTP_WORKFLOW_MGT_HOST',
        'port': 'HTTP_WORKFLOW_MGT_PORT',
        'api_version': 'WORKFLOW_MGT_API_VERSION',
    },
    'conversation_mgt': {
        'host': 'HTTP_CONVERSATION_MGT_HOST',
        'port': 'HTTP_CONVERSATION_MGT_PORT',
        'api_version': 'CONVERSATION_MGT_API_VERSION',
    },
}

def json_request(
    module: str,
    actor: str,
    function: str,
    payload: dict = None,
    method: str = 'POST',
    timeout: int = 5,
    protocol: str = 'http'
):
    """
    動態組出系統內部 API url，並根據指定的 method (預設 POST) 發送 JSON 請求。

    :param protocol: 'http' or 'https' (default: 'http')
    :param module:   模組名稱(對應 MODULE_ENV_MAPPING 的 key, 如 'metadata_mgt')
    :param actor:    要呼叫的 actor (ex: 'MetadataManager')
    :param function: 要呼叫的 function (ex: 'get_conversation_metadata')
    :param payload:  要傳送的 JSON dict (default: None)
    :param method:   'GET', 'POST', 'PUT', 'DELETE' 等 (default: 'POST')
    :param timeout:  請求逾時秒數 (default: 5)
    
    :return:         回傳 requests.Response 物件
    """

    # 防呆，若只想允許 http/https
    if protocol.lower() not in ['http', 'https']:
        raise ValueError(f"Protocol must be 'http' or 'https', got '{protocol}'")

    # 從定義的對應表中抓取環境變數 key
    if module not in MODULE_ENV_MAPPING:
        raise ValueError(f"Unsupported module: {module}")

    env_keys = MODULE_ENV_MAPPING[module]
    host = os.environ.get(env_keys['host'], 'localhost')
    port = os.environ.get(env_keys['port'], '80')
    version = os.environ.get(env_keys['api_version'], 'v1')

    # 組出 API URL
    url = f"{protocol}://{host}:{port}/api/{version}/{module}/{actor}/{function}"

    # 印出做為 debug
    #print(f"[json_request] Sending {method} to: {url}")

    # 根據不同的 method 發送 request
    method = method.upper()
    try:
        if method == 'GET':
            response = requests.get(url, params=payload, timeout=timeout)
        elif method == 'POST':
            response = requests.post(url, json=payload, timeout=timeout)
        elif method == 'PUT':
            response = requests.put(url, json=payload, timeout=timeout)
        elif method == 'DELETE':
            response = requests.delete(url, json=payload, timeout=timeout)
        else:
            raise ValueError(f"HTTP method {method} not supported.")

        response.raise_for_status()  # 如果狀態碼不是 2xx，會丟出異常
        return response

    except requests.exceptions.RequestException as e:
        # 可以在這裡做錯誤處理或 logging
        print(f"Error: {e}")
        raise

async def json_request_async(
    module: str,
    actor: str,
    function: str,
    payload: dict = None,
    method: str = 'POST',
    timeout: int = 60,
    protocol: str = 'http'
) -> httpx.Response:
    """
    非同步 (httpx) 版本：
    動態組出系統內部 API url，並根據指定的 method 發送非同步 JSON 請求。

    :param protocol: 'http' or 'https' (default: 'http')
    :param module:   模組名稱(對應 MODULE_ENV_MAPPING 的 key, 如 'metadata_mgt')
    :param actor:    要呼叫的 actor (ex: 'MetadataManager')
    :param function: 要呼叫的 function (ex: 'get_conversation_metadata')
    :param payload:  要傳送的 JSON dict (default: None)
    :param method:   'GET', 'POST', 'PUT', 'DELETE' 等 (default: 'POST')
    :param timeout:  請求逾時秒數 (default: 5)

    :return:         httpx.Response 物件
    """

    # 防呆，若只想允許 http/https
    if protocol.lower() not in ['http', 'https']:
        raise ValueError(f"Protocol must be 'http' or 'https', got '{protocol}'")

    # 從定義的對應表中抓取環境變數 key
    if module not in MODULE_ENV_MAPPING:
        raise ValueError(f"Unsupported module: {module}")

    env_keys = MODULE_ENV_MAPPING[module]
    host = os.environ.get(env_keys['host'], 'localhost')
    port = os.environ.get(env_keys['port'], '80')
    version = os.environ.get(env_keys['api_version'], 'v1')

    # 組出 API URL
    url = f"{protocol}://{host}:{port}/api/{version}/{module}/{actor}/{function}"
    method = method.upper()

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            if method == 'GET':
                resp = await client.get(url, params=payload)
            elif method == 'POST':
                resp = await client.post(url, json=payload)
            elif method == 'PUT':
                resp = await client.put(url, json=payload)
            elif method == 'DELETE':
                resp = await client.delete(url, json=payload)
            else:
                raise ValueError(f"HTTP method {method} not supported.")

            resp.raise_for_status()
            return resp

        except httpx.RequestError as e:
            print(f"[json_request_async] Error (httpx): {e}")
            raise