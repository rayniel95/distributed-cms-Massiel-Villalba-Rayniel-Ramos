import random

from tools import utils
import os


class DataManager():

    def __init__(self):
        pass

    def add(self, **kwargs):
        raise NotImplementedError()

    def remove(self, **kwargs):
        raise NotImplementedError()

    def get(self, **kwargs):
        raise NotImplementedError()

    def contain(self, **kwargs):
        raise NotImplementedError()

    def get_range(self, **kwargs):
        raise NotImplementedError()

    def remove_range(self, **kwargs):
        raise NotImplementedError()

    def contain_range(self, **kwargs):
        raise NotImplementedError()

    def move(self, **kwargs):
        raise NotImplementedError()

    def move_range(self, **kwargs):
        raise NotImplementedError()


class WidgetManager(DataManager):

    def __init__(self, path: str):
        """

        :param path: path dentro de la app con el nombre del archivo pero sin la extension
        """
        super().__init__()
        self.path = path
        self.api = utils.DBApi(path)
        self.cache = 10

    def add(self, **kwargs):
    #def add(self, id: int, name: str, params: str, state: str, code: str):
        # todo pudiera ser q el codigo fuera un archivo

        hex_id: str = hex(kwargs['id'])

        if not self.api.contain(hex_id, 'widgets'):

            if kwargs['state'] == 'cache':
                self.cache -= 1
                if self.cache <= 0:
                    self._remove_one_cache()

            self.api.add(hex_id, kwargs['name'], kwargs['state'], params=kwargs['params'])
            # creo el archivo y guardo el code
            with open('data{sep}widgets{sep}{name}'.format_map({'sep': os.sep, 'name': kwargs['name']}), 'w') as file:
                try:
                    file.write(kwargs['code'])
                except OSError: print('no se pudo crear el file')

    def remove(self, **kwargs):
    #def remove(self, id: int, name: str):
        hex_id: str = hex(kwargs['id'])

        if self.api.contain(hex_id, 'widgets'):

            if self._get_widget(kwargs['id'])[-1] == 'cache':
                self.cache += 1

            self.api.remove(hex_id, 'widgets')
            name = kwargs['name']
            os.remove(f'data{os.sep}widgets{os.sep}{name}')

    def get(self, **kwargs):
    #def get(self, id: int, name: str):
        hex_id: str = hex(kwargs['id'])

        if self.api.contain(hex_id, 'widgets'):

            code: str
            with open('data{sep}widgets{sep}{name}'.format_map({'sep': os.sep, 'name': kwargs['name']}), 'r') as file:
                try:
                    code = file.read()
                except OSError: print('no se pudo abrir el file')
        # todo pudiera ser q no se pueda tratar con str y se deba usar archivos y trabajar con sendfile

            return self._get_widget(kwargs['id']), code

    def contain(self, **kwargs):
    #def contain(self, id: int):
        if self.api.contain(hex(kwargs['id']), 'widgets'): return True
        return False

    def get_range(self, **kwargs):
    #def get_range(self, start: int, end: int, lexclude: bool, rexclude: bool):

        interval = utils.Interval(kwargs['start'], kwargs['end'], lexclude=kwargs['lexclude'],
                                  rexclude=kwargs['rexclude'])

        for widget in self.api.table_iterator('widgets'):
            if int(widget[0], 16) in interval: yield widget

    def remove_range(self, **kwargs):
    #def remove_range(self, start: int, end: int, lexclude: bool, rexclude: bool):
        widgets_in_range: list = list(self.get_range(start=kwargs['start'], end=kwargs['end'],
                                                     lexclude=kwargs['lexclude'], rexclude=kwargs['rexclude']))

        for widget in widgets_in_range:

            if widget[-1] == 'cache': self.cache += 1

            self.api.remove(widget[0], 'widgets')
            os.remove(f'data{os.sep}widgets{os.sep}{widget[1]}')

    def contain_range(self, **kwargs):
    #def contain_range(self, start: int, end: int, lexclude: bool, rexclude: bool):
        widgets_in_range: list = list(self.get_range(start=kwargs['start'], end=kwargs['end'],
                                                     lexclude=kwargs['lexclude'], rexclude=kwargs['rexclude']))

        if widgets_in_range: return True
        return False

    def move(self, **kwargs):
    #def move(self, id: int, label: str):
        hex_id: str = hex(kwargs['id'])
        if self.api.contain(hex_id, 'widgets'):

            if kwargs['label'] == 'cache':
                self.cache -= 1
                if self.cache <= 0:
                    self._remove_one_cache()

            self.api.change_label(hex_id, 'widgets', kwargs['label'])

    def move_range(self, **kwargs):
    #def move_range(self, start: int, end: int, lexclude: bool, rexclude: bool, label:str):
        widgets_in_range: list = list(self.get_range(start=kwargs['start'], end=kwargs['end'],
                                                     lexclude=kwargs['lexclude'], rexclude=kwargs['rexclude']))

        for widget in widgets_in_range:

            if kwargs['label'] == 'cache':
                self.cache -= 1
                if self.cache <= 0:
                    self._remove_one_cache()

            self.api.change_label(hex(widget[0]), 'widgets', kwargs['label'])

    def _remove_one_cache(self):
        widgets_to_remove: list = []
        for widget in self.api.table_iterator('widgets'):
            if widget[-1] == 'cache': widgets_to_remove.append(widget[0])

        index_to_remove: int = random.randint(0, len(widgets_to_remove) - 1)
        self.cache += 1

        self.api.remove(widgets_to_remove[index_to_remove][0], 'widgets')

    def _get_widget(self, id: int):
        hex_id = hex(id)
        # seria mejor retornar un diccionario o una especie de namespace del modulo args
        for widget in self.api.table_iterator('widgets'):
            if widget[0] == hex_id: return widget

# todo es posible q a causa del dinamismo del anillo y del uso del lock por parte de la base de datos en algun momento
# q se vaya a leer data o a colocar data luego de haber hecho un findsucessor darse cuenta q la data no esta, porque
# halla sido movida, ver bien este caso q aunq parece poco probable no es imposible
class PageManager(DataManager):

    def add(self):
        pass

    def remove(self):
        pass

    def get(self):
        pass

    def contain(self):
        pass

    def get_range(self):
        pass

    def remove_range(self):
        pass

    def contain_range(self):
        pass

    def move(self):
        pass

    def move_range(self):
        pass

    def __init__(self):
        super().__init__()
        raise NotImplementedError()