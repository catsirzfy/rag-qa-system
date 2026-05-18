"""路由注册中心。"""
from dataclasses import dataclass
from app.core.config import settings

@dataclass
class RouteConfig:
    module_path: str; prefix: str; tags: list

CLIENT_ROUTES = [
    RouteConfig("app.api.client.v1.auth", f"{settings.API_V1_STR}/auth", ["Auth"]),
    RouteConfig("app.api.client.v1.chat", f"{settings.API_V1_STR}/chat", ["Chat"]),
]
BACKOFFICE_ROUTES = [
    RouteConfig("app.api.backoffice.v1.admin", f"{settings.API_V1_STR}/admin", ["Admin"]),
]

def register_routes(app, routes):
    for cfg in routes:
        *_, name = cfg.module_path.split(".")
        m = __import__(cfg.module_path, fromlist=[name])
        app.include_router(m.router, prefix=cfg.prefix, tags=cfg.tags)
