from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json

# Adjust to your actual import path
from main.apps.metadata_mgt.services.ImageController import ImageController

class ImageManager:
    @csrf_exempt
    @require_http_methods(["POST"])
    def create_image_metadata(request):
        """
        Input (POST JSON):
        {
            "text_uid": <string>
        }

        Output (JsonResponse):
        {
            "status_code": <int>,
            "status": <bool>,
            "message": <string>,
            "data": {
                "image_uid": <string>,
                "image_path": <string>,   # Will be images/{text_uid}/{image_uid}.png
                "created_at": <string>
            }
        }
        """
        try:
            payload = json.loads(request.body)

            required_fields = ["text_uid"]
            missing = [f for f in required_fields if f not in payload]
            if missing:
                return JsonResponse({
                    "status_code": 400,
                    "status": False,
                    "message": f"Missing field(s): {', '.join(missing)}"
                }, status=400)

            # Call ImageController to create a new image
            response = ImageController.create_image(
                text_uid=payload["text_uid"]
            )

            return JsonResponse(response, status=response["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({
                "status_code": 400,
                "status": False,
                "message": "Invalid JSON"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status_code": 500,
                "status": False,
                "message": str(e)
            }, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    def get_image_metadata(request):
        """
        Input (POST JSON):
        {
            "image_uid": <string>
        }

        Output (JsonResponse):
        {
            "status": <bool>,
            "message": <string>,
            "data": {
                "image_uid": <string>,
                "image_path": <string>,
                "created_at": <string>
            }
        }
        """
        try:
            payload = json.loads(request.body)

            if "image_uid" not in payload:
                return JsonResponse({
                    "status": False,
                    "message": "Missing required field: image_uid"
                }, status=400)

            response = ImageController.get_image_metadata_by_uid(payload["image_uid"])

            return JsonResponse({
                "status": response["status"],
                "message": response["message"],
                "data": response.get("data", {})
            }, status=response["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({
                "status": False,
                "message": "Invalid JSON"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"An error occurred: {str(e)}"
            }, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    def get_image_metadata_list(request):
        """
        Input (POST JSON):
        {
            "text_uid": <string>
        }

        Output (JsonResponse):
        {
            "status": <bool>,
            "message": <string>,
            "data": [
                {
                    "image_uid": <string>,
                    "image_path": <string>,
                    "created_at": <string>
                },
                ...
            ]
        }
        """
        try:
            payload = json.loads(request.body)

            if "text_uid" not in payload:
                return JsonResponse({
                    "status": False,
                    "message": "Missing required field: text_uid"
                }, status=400)

            response = ImageController.get_image_list_by_text_uid(payload["text_uid"])

            return JsonResponse({
                "status": response["status"],
                "message": response["message"],
                "data": response.get("data", [])
            }, status=response["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({
                "status": False,
                "message": "Invalid JSON"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"An error occurred: {str(e)}"
            }, status=500)

    @csrf_exempt
    @require_http_methods(["POST"])
    def delete_image_metadata(request):
        """
        Input (POST JSON):
        {
            "image_uid": <string>
        }

        Output (JsonResponse):
        {
            "status": <bool>,
            "message": <string>
        }
        """
        try:
            payload = json.loads(request.body)

            if "image_uid" not in payload:
                return JsonResponse({
                    "status": False,
                    "message": "Missing required field: image_uid"
                }, status=400)

            response = ImageController.delete_image_by_uid(payload["image_uid"])

            return JsonResponse({
                "status": response["status"],
                "message": response["message"]
            }, status=response["status_code"])

        except json.JSONDecodeError:
            return JsonResponse({
                "status": False,
                "message": "Invalid JSON"
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"An error occurred: {str(e)}"
            }, status=500)
