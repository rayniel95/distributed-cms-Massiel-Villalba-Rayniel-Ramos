import hashlib
import logging
import Pyro4
from Chord.chord.chord import Chord
import threading
from Pyro4 import naming
from tools import managers, ns_workers
import multiprocessing
import sys


logging.basicConfig(level=logging.DEBUG)


class ChordProcess(multiprocessing.Process):
    """
    Hay algunas propiedades a las cuales se pueden acceder y pueden ser utiles antes de iniciar el proceso, pero luego
    de instanciarlo, ya una vez iniciado el proceso hara fork y por tanto no se recomienda acceder a los objetos dentro
    de sus propiedades, puesto q los mismos estaran sujetos a cambios dentro de la memoria del proceso.
    """

    def __init__(self, group=None, target=None, name=None, **kwargs):

        super().__init__(group=group, target=target, name=name)

        self.ns_uri, self.ns_daemon, self.bc_server_daemon = naming.startNS(host=kwargs['host'])

        self.daemon =  Pyro4.Daemon(host=kwargs['host'])

        self.data_manager = managers.DataManager(sys.path[0])

        self.uri_dm = self.daemon.register(self.data_manager)
        self.ns_daemon.nameserver.register('data_manager', self.uri_dm)

        chord_hash = int(hashlib.sha1(bytes('{host}:{port}'.format_map({'host': kwargs['host'],
                                            'port': str(self.uri_dm).split('@')[1].split(':')[1]}),
                                            'utf-8')).hexdigest(), 16)

        self.chord_widgets = Chord(kwargs['host'], int(str(self.uri_dm).split('@')[1].split(':')[1]), chord_hash, 160,
                                   widget=True)

        self.chord_widgets.data_manager_uri = str(self.uri_dm)

        self.chord_widgets.uri = 'PYRO:{name}@{ip}:{port}'.format_map({'name': 'chord_widgets', 'ip': kwargs['host'],
                                                               'port': str(self.uri_dm).split('@')[1].split(':')[1]})


        self.chord_pages = Chord(kwargs['host'], int(str(self.uri_dm).split('@')[1].split(':')[1]), chord_hash, 160,
                                 widget=False)

        self.chord_pages.data_manager_uri = str(self.uri_dm)

        self.chord_pages.uri = 'PYRO:{name}@{ip}:{port}'.format_map({'name': 'chord_pages', 'ip': kwargs['host'],
                                                               'port': str(self.uri_dm).split('@')[1].split(':')[1]})


        daemon_thread = threading.Thread(target=self.daemon_instance, args=(self.daemon,), name='demonio')

        ns_thread = threading.Thread(target=self.name_server_daemon, args=(self.ns_daemon,),
                                     name='demonio del name server')

        bc_thread = threading.Thread(target=self.broadcast_server_daemon, args=(self.bc_server_daemon,),
                                     name='demonio del broadcast')


        daemon_thread.start()
        ns_thread.start()
        bc_thread.start()

    def daemon_instance(self, daemon):

        with daemon as daem:
            daem.requestLoop()


    def broadcast_server_daemon(self, bc_server):

        with bc_server as my_broadcast_server:

            while my_broadcast_server.running:
                my_broadcast_server.processRequest()


    def name_server_daemon(self, ns_daemon):

        with ns_daemon as daemon:
            daemon.requestLoop()


    def go_chord(self, node, type):
        other_ns = ns_workers.NSFinder().get_others_ns()

        if other_ns:
            print(other_ns)
            joiner_uri = ''
            joiner_address = ''
            joiner_id = -1
            joiner_dm_uri = ''

            for uri in other_ns:
                try:
                    with Pyro4.Proxy(uri) as remote_ns:
                        remote_ns._pyroTimeout = 7

                        joiner_uri = remote_ns.lookup('chord_{type}'.format_map({'type': type}))
                        joiner_dm_uri = remote_ns.lookup('data_manager')

                        print('la uri del joiner es' + str(joiner_uri))

                except (Pyro4.errors.TimeoutError, Pyro4.errors.CommunicationError, Pyro4.errors.NamingError):
                    pass

                else: break

            if not joiner_uri: return False

            joiner_address = str(joiner_uri).split('@')[1]
            joiner_id = int(hashlib.sha1(bytes(joiner_address, 'utf-8')).hexdigest(), 16)

            other_node = {'chordId': joiner_id, 'address': joiner_address, 'uri': str(joiner_uri),
                          'manager_uri': str(joiner_dm_uri)}
            print('other node es ' + str(other_node))
            return node.join(other_node)  # puede retornar falso o true si pudo hacer el join correctamente o no, esto
            # hay q meterlo dentro de un ciclo de alguna forma, no da tiempo, hay q entregar algo funcional

        return False
    #
    # def initialize(self):
    #
    #     self.ns_uri, self.ns_daemon, self.bc_server_daemon = naming.startNS(host=self.kwargs['host'])
    #
    #     self.daemon = Pyro4.Daemon(host=self.kwargs['host'])
    #     # __file__.strip('{sep}chord_process.py'.format_map({'sep': os. sep}))
    #     self.data_manager = managers.DataManager('/home/ray/Escritorio/Proyecto de Sistemas Distribuidos Massiel '
    #                                              'Villalba, Rayniel Ramos/CMS')
    #     # todo hay un problema con el path, tiene q hacerse de manera automatica
    #     self.uri_dm = self.daemon.register(self.data_manager)
    #     self.ns_daemon.nameserver.register('data_manager', self.uri_dm)
    #
    #     chord_hash = int(hashlib.sha1(bytes('{host}:{port}'.format_map({'host': self.kwargs['host'],
    #                                                                     'port':
    #                                                                         str(self.uri_dm).split('@')[1].split(':')[
    #                                                                             1]}),
    #                                         'utf-8')).hexdigest(), 16)
    #
    #     self.chord_widgets = Chord(self.kwargs['host'], int(str(self.uri_dm).split('@')[1].split(':')[1]), chord_hash,
    #                                160, widget=True)
    #
    #     uri_widgets = self.daemon.register(self.chord_widgets)
    #     self.ns_daemon.nameserver.register('chord_widgets', uri_widgets)
    #
    #     self.chord_widgets.uri = uri_widgets
    #     self.chord_widgets.data_manager_uri = self.uri_dm
    #
    #     self.chord_pages = Chord(self.kwargs['host'], int(str(self.uri_dm).split('@')[1].split(':')[1]), chord_hash,
    #                              160, widget=False)
    #
    #     uri_pages = self.daemon.register(self.chord_pages)
    #     self.ns_daemon.nameserver.register('chord_pages', uri_pages)
    #
    #     self.chord_pages.uri = uri_pages
    #     self.chord_pages.data_manager_uri = self.uri_dm


    # todo aqi deberia ser run en vez de start pero no se pq da palo
    # cuando llama al run forkea to-do el codigo e intenta meter una copia del demonio q ya se hizo en el mismo puerto

    def go(self):

        to_join = 0
        print('la llave del chord de las paginas es ' + str(self.chord_pages.chordId))
        print('la llave del chord de los widgets es ' + str(self.chord_widgets.chordId))

        while not self.go_chord(self.chord_widgets, 'widgets') and to_join < 3:
            to_join += 1

        if to_join >= 3:
            print('chord de los widgets hace join a none')
            self.chord_widgets.join(None)

        to_join = 0

        while not self.go_chord(self.chord_pages, 'pages') and to_join < 3:
            to_join += 1

        if to_join >= 3:
            print('chord de los pages hace join a none')
            self.chord_pages.join(None)


        stabilizer_widgets = threading.Thread(target=self.chord_widgets.stabilize_forever, name='stabilizer_widgets')

        fixer_finger_widgets = threading.Thread(target=self.chord_widgets.fix_finger_forever,
                                                name='fixer_finger_widgets')

        verifer_topology_widgets = threading.Thread(target=self.chord_widgets.verify_topology_forever,
                                                   name='verifer_topology_widgets')


        stabilizer_pages = threading.Thread(target=self.chord_pages.stabilize_forever, name='stabilizer_pages')

        fixer_finger_pages = threading.Thread(target=self.chord_pages.fix_finger_forever, name='fixer_finger_pages')

        verifer_topology_pages = threading.Thread(target=self.chord_pages.verify_topology_forever,
                                                    name='verifer_topology_pages')


        uri_widgets = self.daemon.register(self.chord_widgets, 'chord_widgets')
        self.ns_daemon.nameserver.register('chord_widgets', self.chord_widgets.uri)



        uri_pages = self.daemon.register(self.chord_pages, 'chord_pages')
        self.ns_daemon.nameserver.register('chord_pages', self.chord_pages.uri)



        stabilizer_widgets.start()
        fixer_finger_widgets.start()
        verifer_topology_widgets.start()

        stabilizer_pages.start()
        fixer_finger_pages.start()
        verifer_topology_pages.start()