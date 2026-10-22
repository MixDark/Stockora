import os
from waitress import serve
from core.wsgi import application

serve(
    application,
    host=os.environ.get("APP_HOST", "0.0.0.0"),
    port=int(os.environ.get("APP_PORT", "7000")),
    trusted_proxy="172.19.0.5",
    trusted_proxy_headers={"x-forwarded-proto"},
)
