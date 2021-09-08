"""Proxy used on the client side which has blocked TCP."""

import threading
import socket
from typing import List, Tuple

from proxy import Proxy, ICMP_BUFFER_SIZE, TCP_BUFFER_SIZE
from icmp import ICMPSocket, ICMP_ECHO_REPLY, ICMPMessage, ICMP_ECHO_REQUEST


class ProxyClient(Proxy, threading.Thread):
    def __init__(self, proxy_hostname: str, sock: socket.socket, dest: Tuple[str, int]):
        threading.Thread.__init__(self)
        self.proxy: str = proxy_hostname
        self.dest: Tuple[str, int] = dest
        self.tcp_socket: socket.socket = sock
        self.icmp_socket: ICMPSocket = ICMPSocket()
        self.sockets = [self.tcp_socket, self.icmp_socket]

    def icmp_data_handler(self, sock):
        message = sock.recvfrom(ICMP_BUFFER_SIZE)
        if message.type == ICMP_ECHO_REPLY:
            self.tcp_socket.send(message.data)

    def tcp_data_handler(self, sock):
        sdata = sock.recv(TCP_BUFFER_SIZE)
        # if no data the socket may be closed/timeout/EOF
        len_sdata = len(sdata)
        code = 0 if len_sdata > 0 else 1
        message = ICMPMessage(type=ICMP_ECHO_REQUEST, code=code,
                              dest_ip=self.dest[0], dest_port=self.dest[1], data=sdata)
        self.icmp_socket.sendto(message, (self.proxy, 1))
        if code == 1:
            self.exit()


class ProxyClientManager(ProxyClient):
    def __init__(self, proxy_server_hostname: str, local_hostname: str, local_port: int, dest_hostname: str, dest_port: int):
        self._proxy_hostname = proxy_server_hostname
        self._local_address = (local_hostname, local_port)
        self._dest_address = (dest_hostname, dest_port)
        self._tcp_server_socket = self.create_tcp_socket(
            self._local_address, server=True)

    # TODO properties

    def run(self):
        while True:
            self._tcp_server_socket.listen(5)
            sock, addr = self._tcp_server_socket.accept()
            newthread = ProxyClient(
                self._proxy_hostname, sock, self._dest_address)
            newthread.start()
