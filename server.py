from tornado.options import define, options
import uuid
import threading
import os.path
import errno
import tornado.websocket
import tornado.web
import tornado.options
import tornado.ioloop
import struct
import json
import tornado.escape
import logging
from zeroconf import ServiceBrowser, Zeroconf, ServiceInfo
import socket
from time import sleep

SERVER_PORT = 9999
SERVER_IP = socket.gethostbyname(socket.gethostname())

zeroconf = Zeroconf()
info = ServiceInfo(
    "_sensor._udp.local.", "Server._sensor._udp.local.", addresses=[
        socket.inet_pton(
            socket.AF_INET, SERVER_IP)
    ], port=SERVER_PORT, priority=0, weight=0
)

zeroconf.register_service(info)

websockets = []


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/", MainHandler),
                    (r"/sensordata", ChatSocketHandler)]
        settings = dict(
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
        )
        super(Application, self).__init__(handlers, **settings)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html", messages=ChatSocketHandler.cache)


class ChatSocketHandler(tornado.websocket.WebSocketHandler):
    waiters = set()
    cache = []
    cache_size = 200

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    def open(self):
        websockets.append(self)

    def on_close(self):
        websockets.remove(self)

    def on_message(self, message):
        logging.info("got message %r", message)


def main():
    app = Application()
    app.listen(8888)

    sock = socket.socket(socket.AF_INET,
                         socket.SOCK_DGRAM)
    sock.bind((SERVER_IP, SERVER_PORT))

    print("Started server at %s:%s" % (SERVER_IP, SERVER_PORT))

    def read_handler(fd, events):
        data, address = sock.recvfrom(1024)
        for ws in websockets:
            ws.write_message(json.dumps(struct.unpack("!Qffffffff", data)))

    tornado.ioloop.IOLoop.current().add_handler(
        sock.fileno(), read_handler, tornado.ioloop.IOLoop.READ)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
