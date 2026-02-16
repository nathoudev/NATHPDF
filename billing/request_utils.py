
# billing/request_utils.py
from fastapi import Request

def get_client_ip(request: Request) -> str:
    # Si tu mets un reverse proxy (Nginx), il enverra X-Forwarded-For
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"
