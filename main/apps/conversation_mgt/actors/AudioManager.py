import os
from pathlib import Path

from django.conf import settings
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from main.utils.ApiKit import json_request
from main.utils.FileKit import create_folder, delete_file
from main.utils.logger import log_trigger

# 音檔大小限制 (50MB，WAV 格式約 30 秒)
MAX_AUDIO_SIZE = 50 * 1024 * 1024


class AudioManager:

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def upload_audio(request):
        """
        前端上傳音檔：
        1. 接收 multipart/form-data（conversation_uid + audio 檔案）
        2. 檢查檔案大小 ≤ 5MB
        3. 呼叫 metadata_mgt 建立 audio metadata
        4. 儲存音檔到 media/audios/{conversation_uid}/{audio_uid}.wav
        5. 回傳 audio_uid
        """
        try:
            conversation_uid = request.POST.get("conversation_uid")
            if not conversation_uid:
                return JsonResponse({
                    "status_code": 400,
                    "message": "Missing required field: 'conversation_uid'"
                }, status=400)

            audio_file = request.FILES.get("audio")
            if not audio_file:
                return JsonResponse({
                    "status_code": 400,
                    "message": "Missing required file: 'audio'"
                }, status=400)

            if audio_file.size > MAX_AUDIO_SIZE:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"File size exceeds limit ({MAX_AUDIO_SIZE // (1024 * 1024)}MB)"
                }, status=400)

            # 呼叫 metadata_mgt 建立 audio metadata
            try:
                meta_resp = json_request(
                    module="metadata_mgt",
                    actor="AudioManager",
                    function="create_audio_metadata",
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

            audio_uid = meta_data["data"]["audio_uid"]
            audio_dir = os.path.join(settings.MEDIA_ROOT, "audios", conversation_uid)
            audio_path = os.path.join(audio_dir, f"{audio_uid}.wav")

            create_folder(audio_dir)
            try:
                with open(audio_path, "wb") as f:
                    for chunk in audio_file.chunks():
                        f.write(chunk)
            except Exception as e:
                return JsonResponse({
                    "status_code": 500,
                    "message": f"Failed to save audio file: {str(e)}"
                }, status=500)

            return JsonResponse({
                "status_code": 201,
                "message": "Audio uploaded successfully",
                "data": {"audio_uid": audio_uid}
            }, status=201)

        except Exception as e:
            return JsonResponse({"status_code": 500, "message": str(e)}, status=500)

    @require_http_methods(["GET"])
    def get_audio(request, audio_uid):
        """
        GET endpoint：供前端 <audio src> 直接播放。
        URL: /api/v3/conversation_mgt/AudioManager/get_audio/<audio_uid>
        透過 DB 查詢 audio_path，直接定位檔案，不做目錄遍歷。
        """
        try:
            meta_resp = json_request(
                module="metadata_mgt",
                actor="AudioManager",
                function="get_audio_metadata",
                payload={"audio_uid": audio_uid}
            )
            meta_data = meta_resp.json()
            if meta_data.get("status_code") != 200:
                raise Http404("Audio not found.")

            audio_path = Path(settings.MEDIA_ROOT) / meta_data["data"]["audio_path"]
            if not audio_path.is_file():
                raise Http404("Audio file not found.")

            return FileResponse(open(audio_path, 'rb'), content_type='audio/wav')
        except Http404:
            return JsonResponse({'error': 'Audio not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def get_audio_list(request):
        """
        取得對話中所有音檔清單。
        """
        import json
        try:
            payload = json.loads(request.body)
            conversation_uid = payload.get("conversation_uid")
            if not conversation_uid:
                return JsonResponse({
                    "status_code": 400,
                    "message": "Missing required field: 'conversation_uid'"
                }, status=400)

            try:
                meta_resp = json_request(
                    module="metadata_mgt",
                    actor="AudioManager",
                    function="get_audio_metadata_list",
                    payload={"conversation_uid": conversation_uid}
                )
                meta_data = meta_resp.json()
            except Exception as e:
                return JsonResponse({
                    "status_code": 502,
                    "message": f"Fail to call metadata_mgt: {str(e)}"
                }, status=502)

            return JsonResponse(meta_data, status=meta_data.get("status_code", 200))

        except json.JSONDecodeError:
            return JsonResponse({"status_code": 400, "message": "無效的 JSON 格式"}, status=400)
        except Exception as e:
            return JsonResponse({"status_code": 500, "message": str(e)}, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def delete_audio(request):
        """
        刪除指定音檔：
        1. 查 metadata_mgt 取得 audio_path。
        2. 刪除音檔檔案。
        3. 刪除 audio metadata。
        """
        import json
        try:
            payload = json.loads(request.body)
            audio_uid = payload.get("audio_uid")
            if not audio_uid:
                return JsonResponse({
                    "status_code": 400,
                    "message": "Missing required field: 'audio_uid'"
                }, status=400)

            # 查詢 metadata 拿 audio_path
            try:
                meta_resp = json_request(
                    module="metadata_mgt",
                    actor="AudioManager",
                    function="get_audio_metadata",
                    payload={"audio_uid": audio_uid}
                )
                meta_data = meta_resp.json()
            except Exception as e:
                return JsonResponse({
                    "status_code": 502,
                    "message": f"Fail to get audio metadata: {str(e)}"
                }, status=502)

            if meta_data.get("status_code") != 200:
                return JsonResponse(meta_data, status=meta_data.get("status_code", 400))

            audio_path = Path(settings.MEDIA_ROOT) / meta_data["data"].get("audio_path")

            if not audio_path or not os.path.exists(audio_path):
                return JsonResponse({
                    "status_code": 404,
                    "message": f"[{audio_path}] Audio file does not exist"
                }, status=404)

            # 刪除音檔
            try:
                delete_file(audio_path)
            except Exception as e:
                return JsonResponse({
                    "status_code": 500,
                    "message": f"Failed to delete audio file: {str(e)}"
                }, status=500)

            # 刪除 metadata
            try:
                del_resp = json_request(
                    module="metadata_mgt",
                    actor="AudioManager",
                    function="delete_audio_metadata",
                    payload={"audio_uid": audio_uid}
                )
                del_data = del_resp.json()
            except Exception as e:
                return JsonResponse({
                    "status_code": 502,
                    "message": f"Fail to delete audio metadata: {str(e)}"
                }, status=502)

            if not del_data.get("status_code", 400):
                return JsonResponse(del_data, status=del_data.get("status_code", 400))

            return JsonResponse({
                "status_code": 200,
                "message": "Audio 刪除成功"
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"status_code": 400, "message": "無效的 JSON 格式"}, status=400)
        except Exception as e:
            return JsonResponse({"status_code": 500, "message": str(e)}, status=500)
