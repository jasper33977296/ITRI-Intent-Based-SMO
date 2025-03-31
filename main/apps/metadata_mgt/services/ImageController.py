import uuid
from django.core.exceptions import ObjectDoesNotExist
from main.apps.metadata_mgt.models.ImageModel import Image
from main.apps.metadata_mgt.models.TextModel import Text

class ImageController:
    @staticmethod
    def create_image(text_uid: str):
        """
        建立一筆新的 Image 資料，並以 text_uid 做關聯。
        回傳格式：
        {
            "status_code": <int>,
            "status": <bool>,
            "message": <str>,
            "data": {
                "image_uid": <str>,
                "image_path": <str>,
                "created_at": <str (ISO8601)>,
            }
        }
        """
        try:
            # 1) 檢查對應的 Text 是否存在
            text_obj = Text.objects.get(text_uid=text_uid)

            # 2) 新增 Image 資料
            new_uuid = uuid.uuid4()
            image_obj = Image.objects.create(
                image_uid=new_uuid,
                f_text_uid=text_obj,
                image_path=f"images/{text_uid}/{new_uuid}.png"
            )

            # 3) 回傳成功資訊
            return {
                "status_code": 201,
                "status": True,
                "message": "Image created successfully.",
                "data": {
                    "image_uid": str(image_obj.image_uid),
                    "image_path": image_obj.image_path,
                    "created_at": image_obj.created_at.isoformat(),
                }
            }

        except Text.DoesNotExist:
            return {
                "status_code": 404,
                "status": False,
                "message": f"Text with uid={text_uid} not found."
            }
        except Exception as e:
            return {
                "status_code": 500,
                "status": False,
                "message": f"Failed to create image: {str(e)}"
            }

    @staticmethod
    def get_image_metadata_by_uid(image_uid: str):
        """
        透過 image_uid 取得單一 Image 資料。
        回傳格式：
        {
            "status_code": <int>,
            "status": <bool>,
            "message": <str>,
            "data": {
                "image_uid": <str>,
                "image_path": <str>,
                "created_at": <str (ISO8601)>,
            }
        }
        """
        try:
            image_obj = Image.objects.get(image_uid=image_uid)
            return {
                "status_code": 200,
                "status": True,
                "message": "Image found.",
                "data": {
                    "image_uid": str(image_obj.image_uid),
                    "image_path": image_obj.image_path,
                    "created_at": image_obj.created_at.isoformat()
                }
            }
        except Image.DoesNotExist:
            return {
                "status_code": 404,
                "status": False,
                "message": f"Image with uid={image_uid} not found."
            }
        except Exception as e:
            return {
                "status_code": 500,
                "status": False,
                "message": f"Failed to retrieve image: {str(e)}"
            }

    @staticmethod
    def get_image_list_by_text_uid(text_uid: str):
        """
        透過 text_uid 取得所有對應的 Image 資料。
        回傳格式：
        {
            "status_code": <int>,
            "status": <bool>,
            "message": <str>,
            "data": [
                {
                    "image_uid": <str>,
                    "image_path": <str>,
                    "created_at": <str (ISO8601)>,
                },
                ...
            ]
        }
        """
        try:
            text_obj = Text.objects.get(text_uid=text_uid)
            images = Image.objects.filter(f_text_uid=text_obj)

            data_list = []
            for img in images:
                data_list.append({
                    "image_uid": str(img.image_uid),
                    "image_path": img.image_path,
                    "created_at": img.created_at.isoformat()
                })

            return {
                "status_code": 200,
                "status": True,
                "message": f"Found {len(data_list)} image(s).",
                "data": data_list
            }
        except Text.DoesNotExist:
            return {
                "status_code": 404,
                "status": False,
                "message": f"Text with uid={text_uid} not found.",
                "data": []
            }
        except Exception as e:
            return {
                "status_code": 500,
                "status": False,
                "message": f"Failed to retrieve image list: {str(e)}",
                "data": []
            }

    @staticmethod
    def delete_image_by_uid(image_uid: str):
        """
        透過 image_uid 刪除一筆 Image 資料。
        回傳格式：
        {
            "status_code": <int>,
            "status": <bool>,
            "message": <str>
        }
        """
        try:
            image_obj = Image.objects.get(image_uid=image_uid)
            image_obj.delete()
            return {
                "status_code": 200,
                "status": True,
                "message": "Image deleted successfully."
            }
        except Image.DoesNotExist:
            return {
                "status_code": 404,
                "status": False,
                "message": f"Image with uid={image_uid} not found."
            }
        except Exception as e:
            return {
                "status_code": 500,
                "status": False,
                "message": f"Failed to delete image: {str(e)}"
            }
