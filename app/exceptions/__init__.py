from fastapi import HTTPException

class NotFoundError(HTTPException):
    def __init__(self, message="资源不存在"): super().__init__(404, message)

class AuthenticationError(HTTPException):
    def __init__(self, message="认证失败"): super().__init__(401, message)

class AuthorizationError(HTTPException):
    def __init__(self, message="权限不足"): super().__init__(403, message)

class ValidationError(HTTPException):
    def __init__(self, message="参数错误"): super().__init__(400, message)
