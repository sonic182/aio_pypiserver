
from aiohttp.web import Request
from aiohttp.web import Response


PYPI = 'https://pypi.org/simple'


async def get_package(request: Request):
    """Get package."""
    headers = {key.decode(): val.decode() for key, val in request.raw_headers}
    package = request.match_info['package']
    request.logger.info('request_info', extra={
        'url': request.url,
        'headers': headers,
        'package': package,
        'method': request.method
    })
    return await fallback_pypi(request, headers, package)
    return Response(text='', status=200)


async def fallback_pypi(request, headers, package):
    """Fallback request to pypi."""
    del headers['Host']
    req_data = {
        'url': PYPI + '/' + package + '/',
        'headers': headers
    }
    function = getattr(request.app['http_session'], request.method.lower())
    request.logger.info('pypi_request', extra=req_data)
    async with function(**req_data) as resp:
        try:
            body = await resp.json()
        except Exception:
            body = await resp.text()
        res_headers = {
            key.decode(): val.decode() for key, val in resp.raw_headers}
        request.logger.info(
            'response', extra={
                'status': resp.status,
                'headers': res_headers,
                'body': body
            })
        del res_headers['Content-Encoding']
        return Response(text=body, status=resp.status, headers=res_headers)
