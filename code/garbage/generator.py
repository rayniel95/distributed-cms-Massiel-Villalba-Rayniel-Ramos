import hashlib
import Pyro4
from flask import render_template_string


class WidgetFinder():

    def __init__(self, chord_widget_uri: str):
        self.chord_widget_uri = chord_widget_uri

    def find(self, *args) -> []:
        """

        :param args: strings con el nombre de los widgets y los parametros instanciados
        :return:
        """
        sucessor: dict = {}
        code = []

        # esto puede dar el palo de q cuando uno este buscado el sucesor este cambie o la red aun no se estabiliza
        with Pyro4.Proxy(self.chord_widget_uri) as my_node:
            for widget in args:
                widget_name = widget.split()[0]

                sucessor = my_node.fin_sucessor(hashlib.sha1(bytes(widget_name, 'utf-8')).hexdigest())

                try:
                    with Pyro4.Proxy(sucessor['manager_uri']) as remote_manager:
                        if remote_manager.exist_tupla(widget_name, widget=True):
                            row = remote_manager.get_row(widget_name, widget=True)
                            code.append(
                                [
                                    (row[0], row[3]),
                                    remote_manager.leer_archivo(widget_name, widget=True)
                                ])

                except (Pyro4.errors.TimeoutError, Pyro4.errors.ConnectionRefusedError,): break

        if len(code) == len(args):
            return code

        return []


class PageGenerator():

    def __init__(self):
        pass

    def _do_dict(self, params: tuple, instances: tuple):
        my_dict: dict = {}

        for key, value in params, instances:
            my_dict[key] = value

        return my_dict

    def gen(self, widgets: tuple, codes: list):
        """

        :param widgets: es una tupla de string con el nombre y los parametros, instanciados, to-do separado por espacio
        :param codes: lista de tuplas de tamano
        :return:
        """
        rendering: list = []

        for index in range(len(codes)):
            pairs = self._do_dict(codes[index][0][1].split(), widgets[index].split()[1:])

            rendering.append(render_template_string(codes[index][1], **pairs))

        return rendering
