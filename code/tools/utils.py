import collections
import os
import sys
import time
from Chord.chord.interval import Interval
from math import pow
import Pyro4, sqlite3


class IntervalCompare:

    def __init__(self, interval: Interval, functionBitNumber: int) -> None:
        self.interval = interval
        self.pot = int(pow(2, functionBitNumber))

    def compare(self, first: dict) -> int:
        if not first: return self.pot

        if self.interval.start < self.interval.end: return first['chordId'] - self.interval.start

        # de otra manera es >=
        if first['chordId'] > self.interval.start: return first['chordId'] - self.interval.start

        if first['chordId'] < self.interval.start: return self.pot - self.interval.start + first['chordId']

        # no se va a dar el caso de la igualdad pq no perteneceria al intervalo


class SucessorList(list):

    def __contains__(self, node: dict) -> bool:
        for sucessor in self.sucessors:
            if sucessor and node['chordId'] == sucessor['chordId']: return True
        return False

    def __init__(self, large: int, list=None) -> None:
        super().__init__()
        self.large = large
        self.sucessors = [None for _ in range(large)] if not list else list

    def __iter__(self):
        return self.sucessors.__iter__()

    def __getitem__(self, item):
        return self.sucessors.__getitem__(item)

    def __setitem__(self, key, value):
        return self.sucessors.__setitem__(key, value)

    def __len__(self):
        return self.large

    def sort(self, *, key=None, reverse=False):

        return self.sucessors.sort(key=key, reverse=reverse)


# todo tener cuidado al pasar y trabajar con las referencias
class Stabilizer:

    def __init__(self):
        pass

    @staticmethod
    def stabilize(sucessors: list, intervalCompare: IntervalCompare, first_sucessor: dict) -> SucessorList:
        # este ciclo se podria reducir a preguntar en vez del intervalo si no son ni mi sucesor ni yo???????
        for index in range(len(sucessors)):
            if sucessors[index] is not None and sucessors[index]['chordId'] not in intervalCompare.interval:
                sucessors[index] = None

        sucessorsList = SucessorList(len(sucessors), sucessors)

        if first_sucessor['chordId'] in intervalCompare.interval and sucessors and first_sucessor not in sucessorsList:
            sucessorsList[-1] = first_sucessor

        sucessorsList.sort(key=intervalCompare.compare)

        return sucessorsList

    @staticmethod
    def deleteDeath(succesorList: SucessorList, intervalCompare: IntervalCompare) -> int:
        # para la mayoria de los casos si el q elimina es el predecesor se puede ahorar el llamado al sucesor para
        # saber si esta vivo, esto es solo optimizacion para evitar overhead en la red
        deaths = 0
        for index in range(len(succesorList)):

            if not succesorList[index]:
                deaths += 1
            else:
                isAlive = False

                try:
                    with Pyro4.Proxy(succesorList[index]['uri']) as remoteNode:
                        remoteNode._pyroTimeout = 3
                        isAlive = remoteNode.ping()
                except (Pyro4.errors.CommunicationError, Pyro4.errors.TimeoutError,):
                    pass
                # esto se puede modificar para obtener un codigo mas bonito

                if not isAlive:
                    succesorList[index] = None
                    deaths += 1

        succesorList.sort(key=intervalCompare.compare)

        return deaths


def first_alive(sucessors: list) -> tuple:
    alive = False

    for item in sucessors:
        if item:
            try:
                with Pyro4.Proxy(item['uri']) as remoteNode:
                    remoteNode._pyroTimeout = 7

                    alive = remoteNode.ping()
            except (Pyro4.errors.CommunicationError, Pyro4.errors.TimeoutError,):
                pass

            if alive: return item, True
    return None, False


class NodeComparer:


    def __init__(self, pot: int):
        self.pot = pot

    def compare(self, node: dict) -> int:
        if not node: return self.pot

        return node['chordId']


# class ProposerTicket:
#     '''
#     clase para hacer un ticket para los proposer, seria un numero q tiene una cota
#     '''
#
#     def __eq__(self, o: object) -> bool:
#         return super().__eq__(o)
#
#     def __ne__(self, o: object) -> bool:
#         return super().__ne__(o)
#
#     def __add__(self, other):
#         pass
#
#     def __cmp__(self, other):
#         pass
#
#     def __iadd__(self, other):
#         pass
#
#     def __ge__(self, other):
#         pass
#
#     def __float__(self):
#         pass
#
#     def __str__(self):
#         pass
#
#     def __abs__(self):
#         pass
#
#     def __divmod__(self, other):
#         pass
#
#     def __gt__(self, other):
#         pass
#
#     def __isub__(self, other):
#         pass
#
#     def __le__(self, other):
#         pass
#
#     def __lt__(self, other):
#         pass
#
#     def __mod__(self, other):
#         pass
#
#     def __neg__(self):
#         pass
#
#     def __init__(self,number: int, top: int):
#         self.number = number
#         self.top = top


class NodeList(list):
    def __init__(self, owner: dict, large: int, pot: int):
        super().__init__()

        self.pot = pot
        self.owner = owner
        self.list = [None for _ in range(large)]
        self.counter_none = large

    def __contains__(self, item: dict):
        if not item or item['chordId'] == self.owner['chordId'] or self._node_in_list(item):
            return True

        return False

    def _node_in_list(self, node: dict):
        for element in self.list:
            if element and element['chordId'] == node['chordId']: return True
        return False

    def add(self, node: dict) -> None:
        if self.counter_none > 0:
            for index in range(len(self.list)):
                if not self.list[index]:
                    self.list[index] = node
                    self.counter_none -= 1
                    return

        else:
            for index in range(len(self.list)):
                with Pyro4.Proxy(self.list[index]['uri']) as remoteNode:
                    try:
                        remoteNode._pyroTimeout = 7
                        remoteNode.ping()
                        self.list[index] = node
                        return
                    except (Pyro4.errors.CommunicationError, Pyro4.errors.TimeoutError,): pass

        self.list[1] = node

    def __iter__(self):
        return self.list.__iter__()

'''
class DBApi:
# todo usar row factory

    path: str

    def __init__(self, path: str):
        self.path = path

    def add(self, id: str, name: str, state: str, **kwargs):
        """

        :param id:
        :param name:
        :param state:
        :param kwargs: table: pages o widgets, si es en widgets agregar params, si es pages agregar head, left, rigth,
                       center, foot
        :return:
        """
        if not kwargs.get('table', False): raise Exception('se debe proveer de una tabla')

        connection = sqlite3.connect('{0}.sqlite3'.format(self.path))
        cursor = connection.cursor()

        if kwargs['table'] == 'pages': cursor.execute('insert into pages values (?,?,?,?,?,?,?,?)',
                                                      (id, name, kwargs.get('head', None), kwargs.get('left', None),
                                                       kwargs.get('rigth', None), kwargs.get('center', None),
                                                       kwargs.get('foot', None), state))

        elif kwargs['table'] == 'widgets': cursor.execute('insert into widgets values (?,?,?,?)',
                                                          (id, name, kwargs.get('params', None), state))

        else:

            connection.commit()
            cursor.close()
            connection.close()

            raise Exception('la tabla no es valida')

        connection.commit()
        cursor.close()
        connection.close()

    def remove(self, id: str, table: str):
        if table != 'pages' or table != 'widgets': raise Exception('la tabla no es valida')

        connection = sqlite3.connect('{0}.sqlite3'.format(self.path))
        cursor = connection.cursor()

        cursor.execute('delete from ? where id=?', (table, id))

        connection.commit()
        cursor.close()
        connection.close()

    def contain(self, id: str, table: str):
        if table != 'pages' or table != 'widgets': raise Exception('la tabla no es valida')

        connection = sqlite3.connect('{0}.sqlite3'.format(self.path))
        cursor = connection.cursor()
        ans: bool = False

        for field in cursor.execute('select id from ?', table):
            if field == id:
                ans = True
                break

        cursor.close()
        connection.close()

        return ans

    def table_iterator(self, table: str) -> collections.Iterator:

        if table != 'pages' or table != 'widgets': raise Exception('la tabla no es valida')
        # todo todo este codigo se puede meter en un contexto
        connection = sqlite3.connect('{0}.sqlite3'.format(self.path))
        cursor = connection.cursor()

        for row in cursor.execute('select * from ?', table):
            yield row

        cursor.close()
        connection.close()

    def change_label(self, id: str, table: str, status: str) -> None:
        if table != 'pages' or table != 'widgets': raise Exception('la tabla no es valida')

        connection = sqlite3.connect('{0}.sqlite3'.format(self.path))
        cursor = connection.cursor()

        cursor.execute('update ? set status=? where id=?', (table, status, id))

        connection.commit()
        cursor.close()
        connection.close()

'''

# region Funciones para testear

def print_finger_table(finger_table: list) -> None:
    for item in finger_table:
        print(
            'start: {0} '
            '\tinterval: {1} '
            '\tchordId: {2} '
            '\taddress: {3} '.format(item['start'], item['interval'], item['node'].get('chordId', None),
                                     item['node'].get('address', None)))


def print_sucessor_list(sucessors: SucessorList) -> None:
    for item in sucessors:
        if item:
            print('chordId: ' + str(item['chordId']) + 'address :' + item['address'])
        else:
            print(None)


def print_node(node: dict) -> None:
    if node:
        print('nodo: chordId: {0}, address: {1}, uri: {2}'.format(node.get('chordId', None), node.get('address', None),
                                                                  node.get('uri', None)))
    else:
        print(None)


def export_finger_table(table: list, sep: str, type: str) -> None:

    with open('{path}{sep}{name}_{type}'.format_map({'path': sys.path[0], 'sep': os.sep, 'name': 'finger_table',
                                                     'type': type}), 'a') as file:

        file.write(sep)
        file.write('\n')
        file.write(str(table))
        file.write('\n')




# endregion
