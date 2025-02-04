from prometheus_client import Counter, Gauge, Histogram, CONTENT_TYPE_LATEST
import time
from aiohttp import web
import prometheus_client


def aiohttp_prometheus(app_name, filter_path_fn=None):
    @web.middleware
    async def middleware_handler(request, handler):
        request_path = request.path
        if filter_path_fn:
            request_path = filter_path_fn(request_path)
        request['start_time'] = time.time()
        request.app['REQUEST_IN_PROGRESS'].labels(app_name, request_path,
                                                  request.method).inc()
        response = await handler(request)
        resp_time = time.time() - request['start_time']
        request.app['REQUEST_LATENCY'].labels(app_name,
                                              request_path).observe(resp_time)
        request.app['REQUEST_IN_PROGRESS'].labels(app_name, request_path,
                                                  request.method).dec()
        request.app['REQUEST_COUNT'].labels(
            app_name, request.method, request_path, response.status).inc()
        return response

    return middleware_handler


async def metrics(request):
    resp = web.Response(body=prometheus_client.generate_latest())
    resp.content_type = CONTENT_TYPE_LATEST
    return resp


def setup_metrics(app, app_name, filter_path_fn=None):
    app['REQUEST_COUNT'] = Counter(
        'requests_total', 'Total Request Count',
        ['app_name', 'method', 'endpoint', 'http_status'])
    app['REQUEST_LATENCY'] = Histogram(
        'request_latency_seconds', 'Request latency', ['app_name', 'endpoint'])

    app['REQUEST_IN_PROGRESS'] = Gauge('requests_in_progress_total',
                                       'Requests in progress',
                                       ['app_name', 'endpoint', 'method'])

    app.middlewares.insert(0, aiohttp_prometheus(app_name, filter_path_fn))
    app.router.add_get("/metrics", metrics)
