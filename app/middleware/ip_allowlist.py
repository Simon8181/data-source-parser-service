from ipaddress import ip_address, ip_network

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class IPAllowlistMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, allowed_entries: list[str]):
        super().__init__(app)
        self.allowed_networks = [ip_network(entry, strict=False) for entry in allowed_entries if entry]

    async def dispatch(self, request: Request, call_next):
        client_host = request.client.host if request.client else ""
        if not client_host:
            return JSONResponse({"detail": "cannot determine client ip"}, status_code=403)

        client_ip = ip_address(client_host)
        if not any(client_ip in network for network in self.allowed_networks):
            return JSONResponse({"detail": f"ip {client_host} not allowed"}, status_code=403)

        return await call_next(request)
