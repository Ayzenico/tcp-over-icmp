"""Module for handling TCP packets."""

import socket


class TCP:

    def __init__(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        