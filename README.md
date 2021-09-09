# tcp-over-icmp
Proxy tunnel of TCP over ICMP

# Instructions
Before use execute 'echo 1 > /proc/sys/net/ipv4/icmp_echo_ignore_all' in order to block ICMP responses

# Usage
Client side: python3 main.py -p <proxy_host> -lh <local_host> -lp <local_port> -dh <dest_host> -dp <dest_port>
Server side: python3 main.py -s
Execute 'python3 main.py -h' for help.
