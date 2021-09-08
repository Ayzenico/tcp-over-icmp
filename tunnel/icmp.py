"""Module for handling ICMP packets."""

import socket
import struct
import binascii
from typing import Optional, Any, Tuple
from dataclasses import dataclass

BARKER = 0xdfdfdf00
BARKER_SIZE = 4
IP_PACK_STR = "BBHHHBBH4s4s"
IP_HEADER_SIZE = 20
ICMP_PACK_STR = "!BBHHHI4sH"

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

    def __init__(self, packet: bytes):
        self.version, self.type, self.len,
        self.host_id, self.flags, self.ttl,
        self.protocol, self.checksum, self.src_ip,
        self.dst_ip = struct.unpack(IP_PACK_STR, packet[:IP_HEADER_SIZE])

    def make_header(self) -> bytes:  # TODO unused probably can delete later
        return struct.pack(IP_PACK_STR, self.version, self.type, self.len,
                           self.host_id, self.flags, self.ttl,
                           self.protocol, self.checksum, self.src_ip, self.dst_ip
                           )


@dataclass
class ICMPMessage:
    ip_header: IPHeader

    # Optional fields will be filled when using ICMPSocket.sendto unless specified otherwise
    type: int = ICMP_ECHO_REQUEST
    code: int = 0
    checksum: Optional[int] = None
    id: int = 0
    sequence: int = 0

    # data
    barker: Optional[int] = None
    dest_ip: str = ''
    dest_port: int = 0
    data: bytes = b''

    def __init__(self, packet: bytes):
        self.ip_header = IPHeader(packet)

        self.type, self.code, self.checksum,
        self.id, self.sequence, self.barker,
        self.dest_ip, self.dest_port, self.data = struct.unpack(
            ICMP_PACK_STR, packet[IP_HEADER_SIZE:])

    def __init__(self, type=ICMP_ECHO_REQUEST, code=0, checksum=None, id=0, sequence=0, barker=None, dest_ip='', dest_port=0, data=b''):
        self.type = type
        self.code = code
        self.checksum = checksum
        self.id = id
        self.sequence = sequence
        self.barker = barker
        self.dest_ip = dest_ip
        self.dest_port = dest_port
        self.data = data

    def make_message(self, make_ip=False) -> bytes:
        ip_header = b''
        if make_ip:
            ip_header = self.ip_header.make_header()

        icmp_header = struct.pack(ICMP_PACK_STR, self.type,
                                  self.code, self.checksum,
                                  self.id, self.sequence,
                                  self.barker, self.dest_ip, self.dest_port)
        return ip_header + icmp_header + self.data

    def calculate_checksum(self):
        packet = self.make_message()
        csum = 0
        countTo = (len(packet) / 2) * 2
        count = 0

        while count < countTo:
            thisVal = ord(packet[count+1]) * 256 + ord(packet[count])
            csum = csum + thisVal
            csum = csum & 0xffffffff
            count = count + 2

        if countTo < len(packet):
            csum = csum + ord(packet[len(packet) - 1])
            csum = csum & 0xffffffff

        csum = (csum >> 16) + (csum & 0xffff)
        csum = csum + (csum >> 16)
        checksum = ~csum
        checksum = checksum & 0xffff
        checksum = checksum >> 8 | (checksum << 8 & 0xff00)
        self.checksum = checksum


class ICMPSocket(socket.socket):

    def __init__(self):
        """Initialize the ICMP socket and set to only receive icmp messages which starts with barker."""

        self.sock = super().__init__(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        # So that each ICMPSocket instance will have a different BARKER
        self._barker = binascii.unhexlify(hex(BARKER + self.fileno())[2:])

    @property
    def barker(self):
        return self._barker

    def recvfrom(self, size: int, flags: int) -> Tuple[bytes, Any]:
        data, address = super().recvfrom(size)
        message = ICMPMessage(data)
        if message.barker != self._barker:
            return None  # Not our message

        return message, address

    def sendto(self, message: ICMPMessage, address: Tuple[bytes, Any]) -> int:
        if not message.barker:
            message.barker = self.barker

        if not message.checksum:
            message.calculate_checksum()

        data = message.make_message()
        data, address = super().sendto(data, address)
