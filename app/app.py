from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.config import Settings, get_settings

settings: Settings = get_settings()

app = FastAPI(
    root_path=settings.api_root_path,
    title=settings.app_title,
)

allowed_origins = ([
        'http://localhost:8888',
        'http://0.0.0.0:8888',
    ]
    # allow localhost ports from 8000-8009
    + [f'http://localhost:{8000+i}' for i in range(10)]
    + [f'http://0.0.0.0:{8000+i}' for i in range(10)]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# stores router
from app.routers import stores
app.include_router(stores.router)

# packets router
from app.routers import packets
app.include_router(packets.router)


@app.get('/', response_class=HTMLResponse)
async def root(request: Request):
    return f"""
        <h1> Hello! Docs available at <a href="{request.scope.get("root_path")}/docs">{request.scope.get("root_path")}/docs</a> </h1>
    """

#
# Healthcheck
#

import logging


# Define the filter
class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.args and \
            len(record.args) >= 3 and \
            record.args[2] != '/health' and \
            not record.args[2].startswith('/metrics')


# Add filter to the logger
logging.getLogger('uvicorn.access').addFilter(EndpointFilter())


# Define the API endpoints
@app.get('/health')
def health():
    return 'I am alive'

#
# Metrics, Traces
#

from app.utils import PrometheusMiddleware, metrics, setting_otlp

# Metrics middleware
app.add_middleware(PrometheusMiddleware, app_name=settings.app_name)
app.add_route('/metrics', metrics)

# OpenTelemetry exporter
setting_otlp(app, settings.app_name, settings.api_trace_url)

