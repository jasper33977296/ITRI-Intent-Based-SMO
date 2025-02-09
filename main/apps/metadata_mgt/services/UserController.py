from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import IntegrityError
from main.apps.metadata_mgt.models.UserModel import User
import django.utils.timezone as timezone

class UserController:

    @staticmethod
    def create_user(user_name, user_password, user_email, user_role=None):
        """
        創建新使用者。
        """
        try:

            hashed_password = make_password(user_password)

            user = User(
                user_name=user_name,
                user_password=hashed_password,
                user_email=user_email,
                user_role=user_role
            )
            user.save()

            return {
                "status_code": 201,
                "status": True,
                "message": f"使用者建立成功",
                "data":{
                    "user_uid":str(user.user_uid)
                }
            }

        except IntegrityError as e:
            return {
                "status_code": 400,
                "status": False,
                "message": f"Email 已存在"
            }

        except ValidationError as e:
            return {
                "status_code": 400,
                "status": False,
                "message": f"驗證失敗: {e.message_dict}"
            }

        except Exception as e:
            return {
                "status_code": 500,
                "status": False,
                "message": f"伺服器內部錯誤: {str(e)}"
            }

    @staticmethod
    def login_user(username, userpassword):
        """
        使用者登入邏輯：
          1. 根據 username 查詢使用者
          2. 驗證密碼
          3. 更新最後登入時間
          4. 回傳結果
        """
        try:
            # 1) 根據 username 取出使用者 (若 Model 欄位叫 user_name，就用 user_name=username)
            user = User.objects.get(user_name=username)
            
            # 2) 驗證密碼 (若 user_password 內存放的是加密後的密碼，需用 check_password)
            if not check_password(userpassword, user.user_password):
                return {
                    "status_code": 400,
                    "status": False,
                    "message": "Invalid password"
                }
            
            # 3) 更新最後登入時間
            user.last_login_time = timezone.now()
            user.save()
            
            # 4) 回傳成功資訊
            return {
                "status_code": 200,
                "status": True,
                "message": "Login successful",
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
                "status": False,
                "message": "User does not exist"
            }

        except Exception as e:
            # 其他預期外錯誤
            return {
                "status_code": 500,
                "status": False,
                "message": f"Server Error: {str(e)}"
            }

    @staticmethod
    def get_user_by_name(user_name):
        """
        根據 user_name 獲取使用者。
        """
        try:
            user = User.objects.get(user_name=user_name)
            return {
                "status_code": 200,
                "status": True,
                "message": (
                    f"使用者查詢成功 "
                    f"(ID={user.user_id}, name={user.user_name}, email={user.user_email})"
                )
            }

        except ObjectDoesNotExist:
            return {
                "status_code": 404,
                "status": False,
                "message": "使用者不存在"
            }

        except Exception as e:
            return {
                "status_code": 500,
                "status": False,
                "message": f"伺服器內部錯誤: {str(e)}"
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
                "status": True,
                "message": f"使用者更新成功"
            }

        except ObjectDoesNotExist:
            return {
                "status_code": 404,
                "status": False,
                "message": "使用者不存在"
            }

        except ValidationError as e:
            return {
                "status_code": 400,
                "status": False,
                "message": f"驗證失敗: {e.message_dict}"
            }

        except Exception as e:
            return {
                "status_code": 500,
                "status": False,
                "message": f"伺服器內部錯誤: {str(e)}"
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
                "status": True,
                "message": f"使用者已刪除 (ID={user_uid})"
            }

        except ObjectDoesNotExist:
            return {
                "status_code": 404,
                "status": False,
                "message": "使用者不存在"
            }

        except Exception as e:
            return {
                "status_code": 500,
                "status": False,
                "message": f"伺服器內部錯誤: {str(e)}"
            }
