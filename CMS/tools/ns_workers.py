import socket
import sys

from Pyro4 import socketutil, config


class NSFinder:
    
    def __init__(self):
        pass
    
    @staticmethod
    def get_all_ns() -> list:
        """
        Method used for get the majority of uris of the names servers.

        :rtype: list
        :return: a list containing names server's uris in the local net, incluiding, if exist, the host's name server. 
        """
        
        # revisar tanto el localhost como hacer broadcast
        remotes_ns = []
      
        # broadcast lookup   
        port = config.NS_BCPORT
        print("broadcast locate")
        sock = socketutil.createBroadcastSocket(reuseaddr=config.SOCK_REUSE, timeout=5.0)

        for _ in range(3):

            for bcaddr in config.parseAddressesString(config.BROADCAST_ADDRS):
                try:
                    sock.sendto(b"GET_NSURI", 0, (bcaddr, port))
                except socket.error as x:
                    err = getattr(x, "errno", x.args[0])
                    # handle some errno's that some platforms like to throw:
                    if err not in socketutil.ERRNO_EADDRNOTAVAIL and err not in socketutil.ERRNO_EADDRINUSE:
                        raise

            try:
                while True:
                    data, _ = sock.recvfrom(100)

                    if sys.version_info >= (3, 0):
                        data = data.decode("iso-8859-1")

                    print("located NS: %s", data)

                    if data not in remotes_ns: remotes_ns.append(data)

            except socket.timeout:
                pass
        
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except (OSError, socket.error):
            pass
            
        sock.close()
        
        return remotes_ns

    @staticmethod
    def get_own_ns() -> str:

        # # first try localhost if we have a good chance of finding it there
        # #sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # sock = socketutil.createSocket(timeout=1.0, reuseaddr=config.SOCK_REUSE)
        #
        # #sock.settimeout(1.0)
        #
        # ns_uri = ''
        # # algunos sistemas Debian usan 127.0.1.1 como localhost, take careful with that
        # for _ in range(3):
        #     sock.sendto(b'GET_NSURI', ('192.168.43.234', 9090))  # direccion de escucha de pedidos broadcast del name server,
        #                             # envia su uri
        #     try:
        #         ns_uri = sock.recv(100)
        #         break
        #     except: pass  # todo esta puede no ser la flag del timeout
        #
        # try:
        #     sock.shutdown(socket.SHUT_RDWR)
        # except (OSError, socket.error,):
        #     pass
        #
        # sock.close()
        #
        # return str(ns_uri)

        my_ip = socketutil.getIpAddress('localhost', workaround127=True)

        for ns_uri in NSFinder.get_all_ns():
            if ns_uri.split('@')[1].split(':')[0] == my_ip:
                return ns_uri

        return ''

    @staticmethod
    def get_others_ns() -> list:
        my_ip = socketutil.getIpAddress('localhost', workaround127=True)

        other_ns = []

        for ns_uri in NSFinder.get_all_ns():
            if ns_uri.split('@')[1].split(':')[0] != my_ip: other_ns.append(ns_uri)

        return other_ns