import os
import json
import requests
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from pathlib import Path

from django.conf import settings

from main.utils.ApiKit import json_request
from main.utils.FileKit import create_folder, delete_file
from main.utils.logger import log_trigger

# 上傳圖片大小限制 (10MB)
MAX_UPLOAD_SIZE = 10 * 1024 * 1024

class ImageManager:

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def upload_image(request):
        """
        前端上傳圖片：
        1. 接收 multipart/form-data（conversation_uid + image 檔案）
        2. 檢查檔案大小 ≤ 10MB、格式為 PNG
        3. 呼叫 metadata_mgt 建立 image metadata
        4. 儲存圖片到 media/images/{conversation_uid}/{image_uid}.png
        5. 回傳 image_uid
        """
        try:
            conversation_uid = request.POST.get("conversation_uid")
            if not conversation_uid:
                return JsonResponse({
                    "status_code": 400,
                    "message": "Missing required field: 'conversation_uid'"
                }, status=400)

            image_file = request.FILES.get("image")
            if not image_file:
                return JsonResponse({
                    "status_code": 400,
                    "message": "Missing required file: 'image'"
                }, status=400)

            # 檢查檔案大小
            if image_file.size > MAX_UPLOAD_SIZE:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"File size exceeds limit ({MAX_UPLOAD_SIZE // (1024*1024)}MB)"
                }, status=400)

            # 檢查檔案格式（PNG）
            if image_file.content_type not in ["image/png"]:
                return JsonResponse({
                    "status_code": 400,
                    "message": "Only PNG format is supported"
                }, status=400)

            # 呼叫 metadata_mgt 建立 image metadata
            try:
                meta_resp = json_request(
                    module="metadata_mgt",
                    actor="ImageManager",
                    function="create_image_metadata",
                    payload={"conversation_uid": conversation_uid}
                )
                meta_data = meta_resp.json()
            except Exception as e:
                return JsonResponse({
                    "status_code": 502,
                    "message": f"Fail to call metadata_mgt: {str(e)}"
                }, status=502)

            if meta_data.get("status_code") != 201:
                return JsonResponse(meta_data, status=meta_data.get("status_code", 400))

            image_uid = meta_data["data"]["image_uid"]
            image_dir = os.path.join(settings.MEDIA_ROOT, "images", conversation_uid)
            image_path = os.path.join(image_dir, f"{image_uid}.png")

            # 建立資料夾並儲存檔案
            create_folder(image_dir)
            try:
                with open(image_path, "wb") as f:
                    for chunk in image_file.chunks():
                        f.write(chunk)
            except Exception as e:
                return JsonResponse({
                    "status_code": 500,
                    "message": f"Failed to save image file: {str(e)}"
                }, status=500)

            return JsonResponse({
                "status_code": 201,
                "message": "Image uploaded successfully",
                "data": {"image_uid": image_uid}
            }, status=201)

        except Exception as e:
            return JsonResponse({"status_code": 500, "message": str(e)}, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def create_image(request):
        """
        建立一筆 image：
        1. 呼叫 metadata_mgt 建立 image metadata。
        2. 將 base64 解碼後儲存為 images/{conversation_uid}/{image_uid}.png。
        """
        try:
            payload = json.loads(request.body)
            
            # (1) 檢查必填欄位
            required_fields = ["conversation_uid", "content"]
            missing = [f for f in required_fields if f not in payload]
            if missing:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"Missing required fields: {', '.join(missing)}"
                }, status=400)
            
            conversation_uid = payload.get("conversation_uid")
            content = payload.get("content")

            # 呼叫 metadata_mgt 建立 image metadata
            try:
                meta_resp = json_request(
                    module="metadata_mgt",
                    actor="ImageManager",
                    function="create_image_metadata",
                    payload={"conversation_uid": conversation_uid}
                )
                meta_data = meta_resp.json()
            except Exception as e:
                return JsonResponse({
                    "status_code": 502,
                    "message": f"Fail to call metadata_mgt: {str(e)}"
                }, status=502)

            if not meta_data.get("status_code", 201):
                return JsonResponse(meta_data, status=meta_data.get("status_code", 400))

            try:
                # 下載圖片
                download_response = requests.get(content, stream=True, timeout=30)
                download_response.raise_for_status()

                image_uid = meta_data["data"]["image_uid"]
                image_dir = os.path.join(settings.MEDIA_ROOT, "images", conversation_uid)
                image_path = os.path.join(image_dir, f"{image_uid}.png")
                
                # 建立資料夾
                create_folder(image_dir)

                with open(image_path, "wb") as f:
                    for chunk in download_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
            except requests.exceptions.RequestException as e:
                return JsonResponse({
                    "status_code": 500,
                    "message": f"Failed to download image from URL {content}: {str(e)}"
                }, status=500)
            except Exception as e: # 捕獲其他可能的文件寫入錯誤
                return JsonResponse({
                    "status_code": 500,
                    "message": f"Failed to save image file locally: {str(e)}"
                }, status=500)

            return JsonResponse({
                "status_code": 201,
                "message": "Image 建立成功",
                "data": {"image_uid": image_uid}
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"status_code": 400, "message": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"status_code": 500, "message": str(e)}, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def get_image_list(request):
        """
        取得指定 conversation 的 image 清單，並讀取對應的實體圖片。
        """
        try:
            payload = json.loads(request.body)
            conversation_uid = payload.get("conversation_uid")

            if not conversation_uid:
                return JsonResponse({
                    "status_code": 400,
                    "message": "Missing required field: 'conversation_uid'"
                }, status=400)

            # 呼叫 metadata_mgt 取得 image metadata list
            try:
                meta_resp = json_request(
                    module="metadata_mgt",
                    actor="ImageManager",
                    function="get_image_metadata_list",
                    payload={"conversation_uid": conversation_uid}
                )
                meta_data = meta_resp.json()
            except Exception as e:
                return JsonResponse({
                    "status_code": 502,
                    "message": f"Fail to call metadata_mgt: {str(e)}"
                }, status=502)

            if not meta_data.get("status_code", 400):
                return JsonResponse(meta_data, status=meta_data.get("status_code", 400))

            image_list = []
            for item in meta_data.get("data", []):
                image_uid = item.get("image_uid")
                image_path = item.get("image_path")

                if not image_uid or not image_path or not os.path.exists(image_path):
                    continue

                image_list.append({
                    "image_uid": image_uid,
                    "image_path": image_path
                })

            return JsonResponse({
                "status_code": 200,
                "message": "Image 查詢清單成功",
                "data": image_list
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"status_code": 400, "message": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"status_code": 500, "message": str(e)}, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def delete_image(request):
        """
        刪除指定 image：
        1. 查 metadata_mgt 取得 image_path。
        2. 刪除圖片檔案。
        3. 刪除 image metadata。
        """
        try:
            payload = json.loads(request.body)
            image_uid = payload.get("image_uid")

            if not image_uid:
                return JsonResponse({
                    "status_code": 400,
                    "message": "Missing required field: 'image_uid'"
                }, status=400)

            # 查詢 metadata 拿 image_path
            try:
                meta_resp = json_request(
                    module="metadata_mgt",
                    actor="ImageManager",
                    function="get_image_metadata",
                    payload={"image_uid": image_uid}
                )
                meta_data = meta_resp.json()
            except Exception as e:
                return JsonResponse({
                    "status_code": 502,
                    "message": f"Fail to get image metadata: {str(e)}"
                }, status=502)

            if meta_data.get("status_code") != 200:
                return JsonResponse(meta_data, status=meta_data.get("status_code", 400))

            image_path = Path(settings.MEDIA_ROOT) / meta_data["data"].get("image_path")

            if not image_path or not os.path.exists(image_path):
                return JsonResponse({
                    "status_code": 404,
                    "message": f"[{image_path}] Image file does not exist"
                }, status=404)

            # 刪除圖片
            try:
                delete_file(image_path)
            except Exception as e:
                return JsonResponse({
                    "status_code": 500,
                    "message": f"Failed to delete image file: {str(e)}"
                }, status=500)

            # 刪除 metadata
            try:
                del_resp = json_request(
                    module="metadata_mgt",
                    actor="ImageManager",
                    function="delete_image_metadata",
                    payload={"image_uid": image_uid}
                )
                del_data = del_resp.json()
            except Exception as e:
                return JsonResponse({
                    "status_code": 502,
                    "message": f"Fail to delete image metadata: {str(e)}"
                }, status=502)

            if not del_data.get("status_code", 400):
                return JsonResponse(del_data, status=del_data.get("status_code", 400))

            return JsonResponse({
                "status_code": 200,
                "message": "Image 刪除成功"
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"status_code": 400, "message": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"status_code": 500, "message": str(e)}, status=500)

    @csrf_exempt 
    @require_http_methods(["POST"])
    @log_trigger()
    def get_image(request):
        try:
            payload = json.loads(request.body)
            
            # (1) 檢查必填欄位
            required_fields = ["conversation_uid", "image_uid"]
            missing = [f for f in required_fields if f not in payload]
            if missing:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"Missing required fields: {', '.join(missing)}"
                }, status=400)
            
            conversation_uid = payload.get("conversation_uid")
            image_uid = payload.get("image_uid")

            # (2) 構建圖片路徑
            image_path = Path(settings.MEDIA_ROOT) / "images" / str(conversation_uid) / f"{image_uid}.png"

            # (3) 檢查檔案是否存在並提供
            if not image_path.is_file():
                print(f"Debug: Image file not found at {image_path}")
                raise Http404("Image not found.")

            return FileResponse(open(image_path, 'rb'), content_type='image/png')
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)
        except Http404 as e:
            print(f"Debug: Http404 caught: {e}")
            return JsonResponse({'error': str(e)}, status=404)
        except FileNotFoundError:
            print(f"Debug: FileNotFoundError during open for {image_path}")
            return JsonResponse({'error': 'Image file not found'}, status=404)
        except Exception as e:
            print(f"Error serving image: {e}")
            return JsonResponse({'error': 'Image could not be served due to server error.'}, status=500)

