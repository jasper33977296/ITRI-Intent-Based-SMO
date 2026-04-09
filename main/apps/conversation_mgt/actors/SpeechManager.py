import os
import uuid
from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from main.utils.logger import log_trigger

# 音檔大小限制 (5MB)
MAX_AUDIO_SIZE = 5 * 1024 * 1024


class SpeechManager:

    @csrf_exempt
    @require_http_methods(["POST"])
    @log_trigger()
    def transcribe(request):
        """
        語音轉文字：
        1. 接收 multipart/form-data（audio 欄位，webm 格式）
        2. 驗證檔案大小 ≤ 5MB
        3. 暫存 webm → pydub 轉 wav → recognize_google(zh-TW)
        4. 刪除暫存檔
        5. 回傳辨識文字
        """
        webm_path = None
        wav_path = None

        try:
            try:
                import speech_recognition as sr
                from pydub import AudioSegment
            except ImportError:
                return JsonResponse({
                    "status_code": 503,
                    "message": "語音辨識模組未安裝，請確認 Docker image 已重新 build 並安裝 SpeechRecognition / pydub"
                }, status=503)

            speech_file = request.FILES.get("speech") 
            if not speech_file:
                return JsonResponse({
                    "status_code": 400,
                    "message": "Missing required file: 'speech'"
                }, status=400)

            # 檢查檔案大小
            if speech_file.size > MAX_AUDIO_SIZE:
                return JsonResponse({
                    "status_code": 400,
                    "message": f"File size exceeds limit ({MAX_AUDIO_SIZE // (1024 * 1024)}MB)"
                }, status=400)

            # 產生暫存檔名：yyyymmdd_hhmmss_4位隨機hex
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            random_hex = uuid.uuid4().hex[:4]
            base_name = f"speech_{timestamp}_{random_hex}"
            webm_path = f"/tmp/{base_name}.webm"
            wav_path = f"/tmp/{base_name}.wav"

            # 儲存暫存 webm
            with open(webm_path, "wb") as f:
                for chunk in speech_file.chunks():
                    f.write(chunk)

            # pydub 轉檔：webm → wav
            audio = AudioSegment.from_file(webm_path, format="webm")
            audio.export(wav_path, format="wav")

            # SpeechRecognition 辨識
            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_path) as source:
                audio_data = recognizer.record(source)

            text = recognizer.recognize_google(audio_data, language="zh-TW")

            return JsonResponse({
                "status_code": 200,
                "message": "Transcription success",
                "data": {"text": text}
            }, status=200)

        except sr.UnknownValueError:
            return JsonResponse({
                "status_code": 422,
                "message": "語音辨識失敗，請重試或手動輸入"
            }, status=422)
        except sr.RequestError as e:
            return JsonResponse({
                "status_code": 502,
                "message": f"語音辨識失敗，請重試或手動輸入"
            }, status=502)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "message": "語音辨識失敗，請重試或手動輸入"
            }, status=500)
        finally:
            # 確保刪除暫存檔
            for path in [webm_path, wav_path]:
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception:
                        pass
