import hashlib

import Pyro4
from tools.managers import DataManager


class Adder():

    def __init__(self, chord_widget_uri: str, chord_page_uri: str):
        self.chord_widget_uri = chord_widget_uri
        self.chord_page_uri = chord_page_uri

    def add(self, name: str, params: str, code: str, widget=True):
        sucessor: dict = {}

        key: int = int(hashlib.sha1(bytes(name, 'utf-8')).hexdigest(), 16)

        with Pyro4.Proxy(self.chord_page_uri) as my_node:

            sucessor = my_node.find_sucessor(key)

        # puede pasar q mientras yo le estoy dando las llaves a quien yo crea q es el sucesor en ese momento, aparezca
        # un nuevo sucesor, yo aun no termino de darle las llaves y entonces el nuevo no las va a tener, asumo q
        # mientras estoy pasando llaves no aparecen nuevos nodos en el sistema. El pseudo no esta del to-do correcto
        # hay q agregar mas cosas a tener en cuenta, pero no tengo tiempo
        try:
            remote_manager: DataManager
            with Pyro4.Proxy(sucessor['manager_uri']) as remote_manager:
                remote_manager.append_item(name, code, widget=widget, params=params, estado='propio')

        except (Pyro4.errors.TimeoutError, Pyro4.errors.ConnectionRefusedError,): return False

        return True

