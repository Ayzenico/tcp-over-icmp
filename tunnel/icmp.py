"""Module for handling ICMP packets."""

import socket
import struct
import random
from typing import Optional, Any, Tuple
from dataclasses import dataclass

# For each socket there is a different barker which is (BARKER + socket.fileno())
# I used random so that multiple clients with different FD tables will be able to use the same server.
BARKER = random.randrange(0, 0xffffff00)
BARKER_SIZE = 4

IP_PACK_STR = "!BBHHHBBH4s4s"
IP_HEADER_SIZE = struct.calcsize(IP_PACK_STR)
ICMP_PACK_STR = "!BBHHHI4sH"
ICMP_HEADER_SIZE = struct.calcsize(ICMP_PACK_STR)

ICMP_ECHO_REQUEST = 8
ICMP_ECHO_REPLY = 0


@dataclass
class IPHeader:
    version: int = 0x45
    type: int = 0
    len: int = 0
    host_id: int = 0
    flags: int = 0
    ttl: int = 128
    protocol: int = 1  # ICMP
    checksum: int = 0
    src_ip: str = ''
    dst_ip: str = ''

    def parse(self, packet: bytes):
        (self.version, self.type, self.len,
        self.host_id, self.flags, self.ttl,
        self.protocol, self.checksum, self.src_ip,
        self.dst_ip) = struct.unpack(IP_PACK_STR, packet[:IP_HEADER_SIZE])
        return self


@dataclass
class ICMPMessage:
    """ICMP message object with our protocol as payload."""

    ip_header: IPHeader

    # Optional fields will be filled when using ICMPSocket.sendto unless specified otherwise
    type: int = ICMP_ECHO_REQUEST
    code: int = 0
    checksum: Optional[int] = None
    id: int = 0
    sequence: int = 0

    # Payload
    barker: Optional[int] = None
    dest_ip: str = ''  # As ascii
    dest_port: int = 0
    data: bytes = b''

    def parse(self, packet: bytes):
        self.ip_header = IPHeader().parse(packet)
        
        (self.type, self.code, self.checksum,
        self.id, self.sequence, self.barker,
        self.dest_ip, self.dest_port) = struct.unpack(
            ICMP_PACK_STR, packet[IP_HEADER_SIZE:IP_HEADER_SIZE + ICMP_HEADER_SIZE])

        self.data = packet[IP_HEADER_SIZE + ICMP_HEADER_SIZE:]
        self.dest_ip = socket.inet_ntoa(self.dest_ip)
        return self

    def __init__(self, type=ICMP_ECHO_REQUEST, code=0, checksum=None, id=0, sequence=0, barker=None, dest_ip='', dest_port=0, data=b''):
        self.type = type
        self.code = code
        self.checksum = checksum
        self.id = id
        self.sequence = sequence
        self.barker = barker
        self.dest_ip = dest_ip
        self.dest_port = int(dest_port)
        self.data = data

    def make_message(self, make_ip=False) -> bytes:
        ip_header = b''
        if make_ip:
            ip_header = self.ip_header.make_header()

        icmp_header = struct.pack(ICMP_PACK_STR, self.type,
                                  self.code, self.checksum,
                                  self.id, self.sequence,
                                  self.barker, socket.inet_aton(self.dest_ip), self.dest_port)
        return ip_header + icmp_header + self.data

    def calculate_checksum(self):
        """
        Calculate and fill the checksum field of ICMP.
        Calculations taken from https://gist.github.com/pklaus/856268 with a few changes.
        """

        self.checksum = 0
        packet = self.make_message()
        csum = 0
        countTo = len(packet) if len(packet) % 2 == 0 else (len(packet) - 1)
        count = 0

        while count < countTo:
            thisVal = packet[count+1] * 256 + packet[count]
            csum = csum + thisVal
            csum = csum & 0xffffffff
            count = count + 2

        if countTo < len(packet):
            csum = csum + packet[len(packet) - 1]
            csum = csum & 0xffffffff

        csum = (csum >> 16) + (csum & 0xffff)
        csum = csum + (csum >> 16)
        checksum = ~csum
        checksum = checksum & 0xffff
        checksum = checksum >> 8 | (checksum << 8 & 0xff00)
        self.checksum = checksum


class ICMPSocket(socket.socket):
    """Proprietary ICMP socket for the proxy."""

    def __init__(self):
        """Initialize the ICMP socket and set to only receive icmp messages which starts with barker."""

        self.sock = super().__init__(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        # So that each ICMPSocket instance will have a different BARKER as an identifier
        self._barker = BARKER + self.fileno()

    @property
    def barker(self):
        return self._barker

    def recvfrom(self, size: int, flags: int = ...) -> Tuple[ICMPMessage, Any]:
        data, address = super().recvfrom(size)
        message = ICMPMessage().parse(data)

        return message, address

    def sendto(self, message: ICMPMessage, address: Tuple[bytes, Any]) -> int:
        if not message.barker:
            message.barker = self.barker

        if not message.checksum:
            message.calculate_checksum()

        data = message.make_message()
        _ = super().sendto(data, address)
