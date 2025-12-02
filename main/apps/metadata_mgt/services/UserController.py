from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import IntegrityError
from main.apps.metadata_mgt.models.UserModel import User
import django.utils.timezone as timezone

class UserController:

    @staticmethod
    def create_user(user_uname, user_password, user_uemail, user_role=None):
        """
        創建新使用者。
        """
        try:

            hashed_password = make_password(user_password)

            user = User(
                user_uname=user_uname,
                user_password=hashed_password,
                user_uemail=user_uemail,
                user_role=user_role
            )
            user.save()

            return {
                "status_code": 201,
                "message": f"使用者建立成功",
                "data":{
                    "user_uid":str(user.user_uid)
                }
            }

        except IntegrityError as e:
            return {
                "status_code": 400,
                "message": f"Email 已存在"
            }

        except ValidationError as e:
            return {
                "status_code": 400,
                "message": f"驗證失敗: {str(e)}"
            }

        except Exception as e:
            return {
                "status_code": 500,
                "message": f"伺服器內部錯誤: {str(e)}"
            }

    @staticmethod
    def login_user(user_uname, user_password):
        """
        使用者登入邏輯：
          1. 根據 user_uname 查詢使用者
          2. 驗證密碼
          3. 更新最後登入時間
          4. 回傳結果
        """
        try:
            # 1) 根據 user_uname 取出使用者 (若 Model 欄位叫 user_name，就用 user_uname=user_uname)
            user = User.objects.get(user_uname=user_uname)
            
            # 2) 驗證密碼 (若 user_password 內存放的是加密後的密碼，需用 check_password)
            if not check_password(user_password, user.user_password):
                return {
                    "status_code": 400,
                    "message": "Invalid password"
                }
            
            # 3) 更新最後登入時間
            user.last_login_time = timezone.now()
            user.save()
            
            # 4) 回傳成功資訊
            return {
                "status_code": 200,
                "message": "使用者登入成功",
                "data": {
                    "user_uid": str(user.user_uid),
                    "last_login_time": (
                        user.last_login_time.strftime("%Y-%m-%d %H:%M:%S")
                        if user.last_login_time else None
                    )
                }
            }

        except ObjectDoesNotExist:
            # 找不到使用者
            return {
                "status_code": 404,
                "message": f"找不到 User"
            }

        except Exception as e:
            # 其他預期外錯誤
            return {
                "status_code": 500,
                "message": f"系統發生錯誤: {str(e)}"
            }

    @staticmethod
    def get_user_by_name(user_uname):
        """
        根據 user_uname 獲取使用者。
        """
        try:
            user = User.objects.get(user_uname=user_uname)
            return {
                "status_code": 200,
                "message": f"使用者查詢成功 email={user.user_uemail}"
            }

        except ObjectDoesNotExist:
            return {
                "status_code": 404,
                "message": f"找不到 User"
            }

        except Exception as e:
            return {
                "status_code": 500,
                "message": f"系統發生錯誤: {str(e)}"
            }


    @staticmethod
    def update_user(user_uid, **kwargs):
        """
        更新使用者資訊。
        """
        try:
            user = User.objects.get(user_uid=user_uid)
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            user.save()

            return {
                "status_code": 200,
                "message": f"使用者更新成功"
            }

        except ObjectDoesNotExist:
            return {
                "status_code": 404,
                "message": f"找不到 User"
            }

        except ValidationError as e:
            return {
                "status_code": 400,
                "message": f"驗證失敗: {e.message_dict}"
            }

        except Exception as e:
            return {
                "status_code": 500,
                "message": f"系統發生錯誤: {str(e)}"
            }


    @staticmethod
    def delete_user(user_uid):
        """
        刪除使用者。
        """
        try:
            user = User.objects.get(user_uid=user_uid)
            user.delete()
            return {
                "status_code": 200,
                "message": "使用者刪除成功"
            }

        except ObjectDoesNotExist:
            return {
                "status_code": 404,
                "message": f"找不到 User"
            }

        except Exception as e:
            return {
                "status_code": 500,
                "message": f"系統發生錯誤: {str(e)}"
            }
