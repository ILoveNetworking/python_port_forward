# This python script used to port forward remote connection
# For example:
# We have our machine "A", server "S" where we running this script and remote network "R" accessible only to server "S" and not to "A"
# So connection will be as follows: A -> S -> R

import socket
import sys
import os
from select import select
from threading import Thread

class PortForward():
    def __init__(self, dst_host : str, dst_port : int, bind_host : str = '0.0.0.0', bind_port : int = 9010) -> None:
        # This is workaround to check either ip or domain name passed to the programm
        # splitting by "." check if every slice is digit and using all() to aggregate and return True if everythin is digit, otherwise return False
        if all([True if i.isdigit() else False for i in bind_host.split(".")]):
            self.bind_host = bind_host
        else:
            self.bind_host = socket.gethostbyname(bind_port)
        
        if all([True if i.isdigit() else False for i in dst_host.split(".")]):
            self.dst_host = dst_host
        else:
            self.dst_host = socket.gethostbyname(dst_host)
        
        self.bind_port = bind_port
        self.dst_port = dst_port

    def __create_socket(self) -> socket.socket:
        """
        This function creates a server listening socket
        """
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((self.bind_host, self.bind_port))
        server_sock.listen()
        ip, port = server_sock.getsockname()
        print(f"[+] Starting port forwarding server at: {ip}:{port}")
        return server_sock
    
    def __connect_to_dst(self) -> socket.socket:
        """
        This function establishes a connection to the target address
        """
        dst_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dst_sock.connect((self.dst_host, self.dst_port))
        return dst_sock
    
    def __handle_client(self, client_sock : socket.socket) -> None:
        """
        Handling client connection, connection to the remote server and run transaction loop
        """
        dst_sock = self.__connect_to_dst()

        while True:
            readable, _, _ = select([client_sock, dst_sock], [], [])

            if not readable:
                break

            for sock in readable:
                if sock is client_sock:
                    data = sock.recv(4096)
                    if dst_sock.send(data) <= 0:
                        return
                else:
                    data = sock.recv(4096)
                    if client_sock.send(data) <= 0:
                        return

    def run(self) -> None:
        """
        This is a main function that runs the Port forwarding, it runs a main listener loop and spawn new thread for a client handler
        """
        server_sock = self.__create_socket()
        while True:
            client_sock, client_addr = server_sock.accept()
            print(f"[+] Forwarding: {client_addr[0]}:{client_addr[1]} -> {self.bind_host}:{self.bind_port} -> {self.dst_host}:{self.dst_port}")
            client_thread = Thread(target = self.__handle_client, args = (client_sock,))
            client_thread.daemon = True
            client_thread.run()

def main() -> None:
    # parse passed arguments here
    # args list must be as follows:
    # port_forward.py <port to run this script on> <target server ip or domain name> <target server port>
    args = sys.argv[1:] # discarding name of the script
    if len(args) != 3:
        print("[!] Invalid number of arguments!")
        print("[+] Usage: port_forward.py <port to run this script on> <target server ip or domain name> <target server port>")
        sys.exit(-1)
    local_port, dest_host, dest_port = args
    try:
        dest_port = int(dest_port)
        local_port = int(local_port)
    except ValueError:
        print("[!] Ports are not an integer!")

    port_fwd = PortForward(dest_host, dest_port, bind_port=local_port)
    port_fwd.run()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[+] Exiting...")
        sys.exit(0)