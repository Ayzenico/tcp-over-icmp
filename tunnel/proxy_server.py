"""Proxy used on the server side which has allowed TCP."""

from proxy import Proxy, ICMP_BUFFER_SIZE, TCP_BUFFER_SIZE
from icmp import ICMPSocket, ICMP_ECHO_REPLY, ICMPMessage, ICMP_ECHO_REQUEST


class ProxyServer(Proxy):
    """The proxy server which will handle TCP connections."""

    def __init__(self):
        self.tcp_sockets = {}
        self.source, self.dest = None, None
        self.icmp_socket = ICMPSocket()
        self.sockets = [self.icmp_socket]

    def icmp_data_handler(self, sock):
        """See base class."""

        message, addr = sock.recvfrom(ICMP_BUFFER_SIZE)
        if not message:
            return
        self.source = addr[0]
        self.dest = (message.dest_ip, message.dest_port)
        if message.type == ICMP_ECHO_REPLY:
            # our packet, do nothing
            pass
        elif message.type == ICMP_ECHO_REQUEST and message.code == 1:
            # End connection
            if message.barker in self.tcp_sockets:
                self.sockets.remove(self.tcp_sockets[message.barker])
                self.tcp_sockets[message.barker].close()
                del self.tcp_sockets[message.barker]
        elif message.type == ICMP_ECHO_REQUEST and message.code == 0:
            # Handle client request
            if message.barker not in self.tcp_sockets:
                # New connection
                self.tcp_sockets[message.barker] = self.create_tcp_socket(self.dest)
                self.sockets.append(self.tcp_sockets[message.barker])
            self.tcp_sockets[message.barker].send(message.data)
        else:
            # Unknown ICMP format
            print("Received bad ICMP packet")

    def tcp_data_handler(self, sock):
        """See base class."""

        try:
            sdata = sock.recv(TCP_BUFFER_SIZE)
        except OSError:
            if sock in self.sockets:
                self.remove_tcp_socket(sock)

        for _barker, _socket in self.tcp_sockets.items():
            if _socket == sock:
                sock_barker = _barker

        # if no data the socket may be closed/timeout/EOF
        code = 0 if len(sdata) > 0 else 1
        message = ICMPMessage(type=ICMP_ECHO_REPLY, code=code, dest_ip=self.dest[0], dest_port=self.dest[1], data=sdata, barker=sock_barker)
        self.icmp_socket.sendto(message, (self.source, 0))

        if code == 1:
            self.remove_tcp_socket(sock)

    def remove_tcp_socket(self, sock):
        self.sockets.remove(sock)
        for k,v in self.tcp_sockets.items():
            if v == sock:
                del self.tcp_sockets[k]
                return
        self.sock.close()