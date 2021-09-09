import argparse

from proxy_server import ProxyServer
from proxy_client import ProxyClientManager


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Python TCP over ICMP tunnel.",
        usage="""Needs to be runned as root (use of raw sockets), currently support only IP addresses.
                Client side: python3 main.py -p <proxy_host> -lh <local_host> -lp <local_port> -dh <dest_host> -dp <dest_port>
                Server side: python3 main.py -s""",
    )

    parser.add_argument("-s", "--server", action="store_true", default=False,
                        help="Set proxy mode")
    parser.add_argument("-p", "--proxy_host",
                        help="Host on which the proxy is running")
    parser.add_argument("-lh", "--local_host", default="127.0.0.1",
                        help="(local) Listen ip for incomming TCP connections,"
                        "default 127.0.0.1")
    parser.add_argument("-lp", "--local_port", type=int,
                        help="(local) Listen port for incomming TCP connections")
    parser.add_argument("-dh", "--destination_host",
                        help="Specifies the remote host to send your TCP connection")
    parser.add_argument("-dp", "--destination_port", type=int,
                        help="Specifies the remote port to send your TCP connection")

    args = parser.parse_args()

    if args.server:
        print("Started server.")
        tunnel = ProxyServer()
    else:
        print("Started client proxy.")
        tunnel = ProxyClientManager(
            proxy_server_hostname=args.proxy_host,
            local_hostname=args.local_host, local_port=args.local_port,
            dest_hostname=args.destination_host, dest_port=args.destination_port
        )

    tunnel.run()


if __name__ == "__main__":
    main()
