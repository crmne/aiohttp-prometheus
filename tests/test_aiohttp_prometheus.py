import asyncio

from aiohttp import web
from aiohttp.test_utils import TestClient as _TestClient
from aiohttp.test_utils import loop_context

import pytest
from aiohttp_prometheus import setup_metrics


@pytest.fixture
def app():
    app = web.Application()
    setup_metrics(app, 'test_app')
    return app


@pytest.yield_fixture
def loop():
    with loop_context() as loop:
        yield loop


@pytest.yield_fixture
def test_client(loop, app):
    client = _TestClient(app, loop=loop)
    loop.run_until_complete(client.start_server())
    yield client
    loop.run_until_complete(client.close())


def test_metrics_route(loop, test_client):
    @asyncio.coroutine
    def test_get_metrics():
        resp = yield from test_client.request('GET', '/metrics')
        assert resp.status == 200
        text = yield from resp.text()
        assert 'request_latency_seconds' in text
        assert 'requests_total' in text
        assert 'requests_in_progress' in text

    loop.run_until_complete(test_get_metrics())
