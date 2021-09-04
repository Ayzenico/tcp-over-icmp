"""Module for handling ICMP packets."""

import scapy
import socket


class ICMP:

    def __init__(self, barker):
        """Initialize the ICMP socket and set to only receive icmp messages which starts with barker.
        
        Args:
            barker (str): Barker to filter the ICMP packets by.
        """
        
        self._barker = barker
        self._sock = socket.socket(socket.AF_INET)

    @property
    def barker(self):
        return self._barker
    
    def recv_icmp():
        pass

    def send_icmp():
        pass