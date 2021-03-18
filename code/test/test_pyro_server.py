import Pyro4
from Pyro4 import socketutil, naming
import threading


@Pyro4.expose
class Tester():

    def __init__(self):
        pass

    def hello(self):
        return 'hello'


def daemon_instance(daemon):
    """

    :param object_class: lista de objetos o clases a registrar en el demonio
    :param uris: lista vacia donde se dejaran las uris de cada objeto de la lista de object_class
    :return: nada, entra en un eventloop
    """

    with daemon as daem:
        daem.requestLoop()


def broadcast_server_daemon(bc_server):

    my_broadcast_server: naming.BroadcastServer

    with bc_server as my_broadcast_server:

        while my_broadcast_server.running:
            my_broadcast_server.processRequest()


def name_server_daemon(ns_daemon):

    with ns_daemon as daemon:
        daemon.requestLoop()


def main():
    uris_list = []

    ns_uri, ns_daemon, bc_server = naming.startNS(socketutil.getIpAddress('localhost', workaround127=True))

    daemon = Pyro4.Daemon(socketutil.getIpAddress('localhost', workaround127=True))

    algo1 = Tester()
    algo2 = Tester()

    for item in [algo1]:
        uri = daemon.register(item, 'algo')
        uris_list.append(uri)  # se dejan las uris en una lista

    daemon_thread = threading.Thread(target=daemon_instance, args=(daemon,), name='demonio')
    daemon_thread.start()

    print(ns_uri)
    print(uris_list)

    for uri in uris_list:
        print(uri)
        ns_daemon.nameserver.register('tester', uri)

    ns_thread = threading.Thread(target=name_server_daemon, args=(ns_daemon,), name='demonio del name server')

    bc_thread = threading.Thread(target=broadcast_server_daemon, args=(bc_server,), name='demonio del broadcast')

    ns_thread.start()
    bc_thread.start()



if __name__ == '__main__':
    main()