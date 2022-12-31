import uvicorn
import os


abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

from app.config import Settings, get_settings
settings: Settings = get_settings()


from app.app import app

if __name__ == "__main__":
    # update uvicorn access logger format
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["access"]["fmt"] = "%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s resource.service.name=%(otelServiceName)s] - %(message)s"
    uvicorn.run(app, host="0.0.0.0", port=settings.api_http_port, log_config=log_config)
