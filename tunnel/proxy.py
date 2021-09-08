"""Implements base class for the proxy."""

import socket
import select


# TODO change
ICMP_BUFFER_SIZE = 1500
TCP_BUFFER_SIZE = 1500


class Proxy:
    @staticmethod
    def create_tcp_socket(dest, server=False):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(dest) if server else sock.connect(dest)
        return sock

    def icmp_data_handler(self, sock):
        raise NotImplementedError

    def tcp_data_handler(self, sock):
        raise NotImplementedError

    def run(self):
        try:
            while True:
                sread, _, _ = select.select(self.sockets, [], [])
                for sock in sread:
                    if sock.proto == socket.IPPROTO_ICMP:
                        print("Received icmp.")
                        self.icmp_data_handler(sock)
                    else:
                        print("Received tcp.")
                        self.tcp_data_handler(sock)
        except:
            raise
        finally:
            self.close()

    def close(self):
        for socket in self.sockets:
            socket.close()
