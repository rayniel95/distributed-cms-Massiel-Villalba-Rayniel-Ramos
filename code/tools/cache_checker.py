import Pyro4
from time import sleep
from hashlib import sha1
from tools import ns_workers

cache_title = 'probando cache chequer '

class CacheCheckerPages():

    def __init__(self, name, params):
        self.condition_continue = True

        own_ns_uri = ns_workers.NSFinder().get_own_ns()

        with Pyro4.Proxy(own_ns_uri) as my_ns:
            self._uri_chord_page = my_ns.lookup('chord_pages')
            self._uri_mi_manager = my_ns.lookup('data_manager')

        self._uri_mi_manager = str(self._uri_mi_manager)
        self._uri_chord_page = str(self._uri_chord_page)

        self._params = params
        self._name = name
        self._hashy = int(sha1(bytes(self._name, 'utf-8')).hexdigest(), 16)

    # al final como dijo la mejor idea es ponerlo en el mismo archivo aqellos q lo pidieron para despues hacerles push
    # esto puede ser otro proceso y la condicion ser un shared value
    def ask_for_params_change(self):

        while (self.condition_continue):
            try:
                with Pyro4.Proxy(self._uri_chord_page) as chord_page:
                    chord_page._pyroTimeout = 7

                    node = chord_page.find_sucessor(self._hashy)

            except (Pyro4.errors.ConnectionRefusedError, Pyro4.errors.TimeoutError, Pyro4.errors.CommunicationError,):
                continue

            uri_manager = node['manager_uri']

            if uri_manager != self._uri_mi_manager:
                try:
                    with Pyro4.Proxy(uri_manager) as remote_manager:
                        remote_manager._pyroTimeout = 7

                        real_params = remote_manager.query("params", "page", where=" where name='" + self._name + "'")[
                            0][0]

                        if real_params != self._params:
                            code = remote_manager.leer_archivo(self._name, widget=False)

                            with Pyro4.Proxy(self._uri_mi_manager) as mi_manager:
                                mi_manager._pyroTimeout = 7
                                # append_item(self,name,estado,params,code,widget = True)
                                mi_manager.append_item(self._name, code, widget=False, params=real_params,
                                                       estado="cache")

                except (Pyro4.errors.ConnectionRefusedError, Pyro4.errors.TimeoutError,
                        Pyro4.errors.CommunicationError,): pass

            sleep(3)