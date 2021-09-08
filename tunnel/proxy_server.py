"""Proxy used on the server side which has allowed TCP."""

from proxy import Proxy, ICMP_BUFFER_SIZE, TCP_BUFFER_SIZE
from icmp import ICMPSocket, ICMP_ECHO_REPLY, ICMPMessage, ICMP_ECHO_REQUEST


class ProxyServer(Proxy):
    def __init__(self):
        self.tcp_socket = None
        self.source, self.dest = None, None
        self.icmp_socket = ICMPSocket()
        self.sockets = [self.icmp_socket]

    def icmp_data_handler(self, sock):
        message, addr = sock.recvfrom(ICMP_BUFFER_SIZE)
        self.source = addr[0]
        self.dest = (message.dest_ip, message.dest_port)
        if message.type == ICMP_ECHO_REPLY and message.code == 0:
            # our packet, do nothing
            pass
        elif message.type == ICMP_ECHO_REQUEST and message.code == 1:
            # control
            self.sockets.remove(self.tcp_socket)
            self.tcp_socket.close()
            self.tcp_socket = None
        elif message.type == ICMP_ECHO_REQUEST and message.code == 0:
            if not self.tcp_socket:
                self.tcp_socket = self.create_tcp_socket(self.dest)
                self.sockets.append(self.tcp_socket)
            self.tcp_socket.send(message.data)
        else:
            print("Received bad ICMP packet")

    def tcp_data_handler(self, sock):
        sdata = sock.recv(TCP_BUFFER_SIZE)
        message = ICMPMessage(type=ICMP_ECHO_REPLY, code=0, dest_ip=self.dest[0], dest_port=self.dest[1], data=sdata)
        self.icmp_socket.sendto(message, (self.source, 0))
