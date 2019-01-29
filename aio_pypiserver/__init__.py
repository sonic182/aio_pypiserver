"""Main module."""

from uuid import uuid4
from argparse import ArgumentParser
from configparser import ConfigParser

from aio_pypiserver.utils import get_logger

import aiohttp.web
from aiohttp.web import middleware

from aio_pypiserver import handlers
from aio_pypiserver.utils import Logger


@middleware
async def req_middleware(request, handler):
    request.logger = Logger(
        request.app.logger.logger, {'uuid': uuid4().hex})
    return await handler(request)


async def on_startup(app):
    """Setup startup stuffs."""
    http = app['config']['http']
    app['http_session'] = aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(
            sock_read=http.getint('read_timeout', fallback=27),
            sock_connect=http.getint('conn_timeout', fallback=3),
        ),
        connector=aiohttp.TCPConnector(
            limit=http.getint('limit', 30),
            ssl=http.getboolean('ssl', True),
        )
    )


async def on_cleanup(app):
    """Setup cleanup stuffs."""
    await app['http_session'].close()


def get_app(logger, args, config):
    """Get configured app."""
    app = aiohttp.web.Application(logger=logger, debug=args.debug,
                                  middlewares=[req_middleware])
    app['config'] = config

    prefix = args.prefix
    app.router.add_get(prefix + '/{package}/', handlers.get_package)

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    return app


def start(logger, args, config):
    """Start script."""
    app = get_app(logger, args, config)

    try:
        params = {'port': args.port, 'host': args.host}
        logger.info('starting_app', extra=params)
        aiohttp.web.run_app(app)
    except KeyboardInterrupt:
        logger.info('exit_app')


def get_arguments():
    parser = ArgumentParser()
    parser.add_argument('-c', '--config', default='./config.ini')
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-p', '--port', type=int, default=8080)
    parser.add_argument('-H', '--host', type=str, default='localhost')
    parser.add_argument('-P', '--prefix', type=str, default='/simple')
    return parser.parse_args()


def main():
    """Start script."""
    args = get_arguments()
    config = ConfigParser()
    config.add_section('logging')
    config.add_section('http')
    config.read(args.config)
    logger, uuid = get_logger(args, config)
    get_logger(args, config, None, 'aiohttp.access')
    logger.info('Starting script...')
    start(logger, args, config)
    logger.info('Exiting Server...')


if __name__ == '__main__':
    main()
