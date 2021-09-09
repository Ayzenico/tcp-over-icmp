"""Proxy used on the client side which has blocked TCP."""

import threading
import socket
from typing import Tuple

from proxy import Proxy, ICMP_BUFFER_SIZE, TCP_BUFFER_SIZE
from icmp import ICMPSocket, ICMP_ECHO_REPLY, ICMPMessage, ICMP_ECHO_REQUEST


class ProxyClient(Proxy, threading.Thread):
    """Proxy client on the blocked TCP side."""

    def __init__(self, proxy_hostname: str, sock: socket.socket, dest: Tuple[str, int]):
        threading.Thread.__init__(self)
        self.proxy: str = proxy_hostname
        self.dest: Tuple[str, int] = dest
        self.tcp_socket: socket.socket = sock
        self.icmp_socket: ICMPSocket = ICMPSocket()
        self.sockets = [self.tcp_socket, self.icmp_socket]

    def icmp_data_handler(self, sock):
        """See base class."""

        message, _ = sock.recvfrom(ICMP_BUFFER_SIZE)
        if not message:
            return
        if message.barker == self.icmp_socket.barker:
            if message.type == ICMP_ECHO_REPLY and message.code == 1:
                self.close()
                exit()
            elif message.type == ICMP_ECHO_REPLY:
                self.tcp_socket.send(message.data)

    def tcp_data_handler(self, sock):
        """See base class."""

        sdata = sock.recv(TCP_BUFFER_SIZE)
        # if no data the socket may be closed/timeout/EOF
        code = 0 if len(sdata) > 0 else 1
        message = ICMPMessage(type=ICMP_ECHO_REQUEST, code=code,
                              dest_ip=self.dest[0], dest_port=self.dest[1], data=sdata)
        self.icmp_socket.sendto(message, (self.proxy, 1))
        if code == 1:
            self.close()
            exit()


class ProxyClientManager(ProxyClient):
    """Manager of all ProxyClient instances."""

    def __init__(self, proxy_server_hostname: str, local_hostname: str, local_port: int, dest_hostname: str, dest_port: int):
        self._proxy_hostname = proxy_server_hostname
        self._local_address = (local_hostname, local_port)
        self._dest_address = (dest_hostname, dest_port)
        self._tcp_server_socket = self.create_tcp_socket(
            self._local_address, server=True)

    def run(self):
        while True:
            self._tcp_server_socket.listen(5)
            sock, _= self._tcp_server_socket.accept()
            newthread = ProxyClient(
                self._proxy_hostname, sock, self._dest_address)
            newthread.start()
