from collections import namedtuple
from time import sleep
from zeroconf import ServiceBrowser, Zeroconf, ServiceInfo
import socket
import struct
import threading
import time
import random

Dest = namedtuple('dest', ['ip', 'port'])


class SensorStreamThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.socket = socket.socket(socket.AF_INET,
                                    socket.SOCK_DGRAM)
        self.destinations = []

    def add_destination(self, destination):
        self.destinations.append(destination)

    def rm_destination(self, destination):
        self.destinations.remove(destination)

    def run(self):
        while (True):
            for dest in self.destinations:
               # print('sending to %s', dest)
                sensors = [time.time_ns(), random.uniform(0, 10), 1.2, 1.3, 1.4,
                           1.5, 1.6, 1.7, 1.8]
                self.socket.sendto(
                    struct.pack("!Qffffffff", *sensors), (dest.ip, dest.port))
                sleep(0.01)


class ZeroConfListener:
    def __init__(self):
        self.streamer = SensorStreamThread()
        self.streamer.start()

    def remove_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        print("Service %s removed, $s" % (name, info))
        self.streamer.rm_destination(Dest(
            ip=info.addresses[0], port=info.port))

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        print("Sensor sink %s added, service info: %s" % (name, info))
        self.streamer.add_destination(Dest(
            ip=socket.inet_ntoa(info.addresses[0]), port=info.port))


zeroconf = Zeroconf()
listener = ZeroConfListener()
browser = ServiceBrowser(zeroconf, "_sensor._udp.local.", listener)

try:
    input("Press enter to exit...\n\n")
finally:
    zeroconf.close()
