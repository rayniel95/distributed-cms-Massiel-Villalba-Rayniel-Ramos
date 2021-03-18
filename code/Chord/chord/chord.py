import hashlib
import time
from math import pow
import random
from tools import ns_workers

import Pyro4

from Chord.dht.dht import DHT
from tools import utils
from Chord.chord.interval import Interval

fix_finger_title = 'ejecutando fix_finger: '
stabilize_title = 'ejecutando stabilize: '
notify_title = 'ejecutando notify: '

@Pyro4.expose
class Chord(DHT):

    def __init__(self, ip: str, port: int, ID: int, functionBitNumber:int, widget=True):
        super(Chord, self).__init__()

        self.sucessor_list_size = 3
        self.sucessor_list = utils.SucessorList(self.sucessor_list_size)
        self.widget = widget
        self._functionBitNumber = functionBitNumber
        self.port = port
        self.ip = ip
        self._chordId = ID
        self._uri = None
        self._ns_uri = None
        self._ns = None

        self._data_manager_uri = None
        self._pot = int(pow(2, self._functionBitNumber))

        self.node_list = utils.NodeList({'chordId': self._chordId, 'address': self.address, 'uri': self.uri,
                                         'manager_uri': self.data_manager_uri}, 10, self._pot)
        # la 3ra columna es un diccionario, chordId:int con el ip:puerto en str, y el uri del nodo, uri del data manager
        self._fingerTable = []

        startIndex = int((self._chordId + pow(2, 0)) % self._pot)
        startIndexPlus = int((self._chordId + pow(2, 1)) % self._pot)  # tengo q ver si esta suma es correcta

        for index in range(self._functionBitNumber):
            self._fingerTable.append({'start': startIndex, 'interval': Interval(startIndex, startIndexPlus,
                                                                                rexclude=True),
                                      'node': {}})

            startIndex = startIndexPlus
            startIndexPlus = int((self._chordId + pow(2, index + 2)) % self._pot)

        self._sucessor = None
        self._predecessor = None

    @property
    def data_manager_uri(self) -> str:
        return self._data_manager_uri

    @data_manager_uri.setter
    def data_manager_uri(self, value: str) -> None:
        self._data_manager_uri = value

    @property
    def chordId(self) -> int:
        return self._chordId

    @property
    def uri(self):
        return self._uri

    @uri.setter
    def uri(self, value: str):
        '''
        hay q setearlo inmediatamente despues de registrarlo en el demonio
        :type value: str
        :param value: el valor de la uri
        :return: None
        '''
        self._uri = value

    @property
    def ns_uri(self):
        return self._ns_uri

    @ns_uri.setter
    def ns_uri(self, value):
        self._ns_uri = value

    @property
    def name_server(self):
        return self._ns

    @name_server.setter
    def name_server(self, value):
        self._ns = value

    @property
    def address(self) -> str:
        return self.ip + ':' + str(self.port)

    @property
    def sucessor(self) -> dict:

        return self._sucessor

    @sucessor.setter
    def sucessor(self, value: dict):
        self._sucessor = value

    @property
    def get_sucessor_list(self):
        return self.sucessor_list  # todo revisar q devuelva una lista no una sucesor list

    @property
    def predecessor(self) -> dict:
        return self._predecessor

    @predecessor.setter
    def predecessor(self, value: dict):
        self._predecessor = value

    def get(self, key: list) -> 'codigo, lo pone en alguna parte':
        # busco el sucesor de esa llave, una vez lo encuentre abro un proxy y que me envie en codigo
        # tiene q ser una lista de llaves y ser un metodo asincrono o onewaycall
        # tiene q haber algun mecanismo tambien para cuando yo vaya a guardar y de repente el tipo se muere, volver a
        # encontrar ahora el sucesor de esa llave y darselo a otro
        pass

    def set(self, key: list):
        # se consigue el sucesor de todas esas llaves y se les sube el codigo, con to-do esto hay q verificar q el
        # codigo le haya llegado y correcto si no volverlo a enviar
        pass

    def find_sucessor(self, key: int) -> dict:
        predecessor = self.find_predecessor(key)

        if len(predecessor) > 0:  # verdaderamente no importa si me dan un zombi
            answer = {}

            try:  # verificar q sigue vivo
                with Pyro4.Proxy(predecessor['uri']) as remoteNode:
                    remoteNode._pyroTimeout = 7

                    answer = remoteNode.sucessor

            except (Pyro4.errors.CommunicationError, Pyro4.errors.TimeoutError,): return {}

            # todo si la finger table del nodo esta vacia o no encuentra nada pq aun no se actualiza, hay q preguntarle
            # al sucesor usando el puntero
            return answer  # todo asegurarme de q el dict sea accesible sin intermediarios
        return {}

    def find_predecessor(self, key: int) -> dict:
        actualNode = {'chordId': self.chordId, 'address': self.address, 'uri': self.uri,
                      'manager_uri': self.data_manager_uri}

        actualNodeId = self.chordId
        actualNodeSucessorId = self.sucessor['chordId']

        while len(actualNode) > 0 and key not in Interval(actualNodeId, actualNodeSucessorId, lexclude=True):
            # actualNode puede estar muerto
            try:
                with Pyro4.Proxy(actualNode['uri']) as remoteNode:
                    remoteNode._pyroTimeout = 7
                    actualNode = remoteNode.closest_preceding_finger(key)

            except (Pyro4.errors.CommunicationError, Pyro4.errors.TimeoutError,): actualNode = {}
            # esta muerto, preguntarle a mi sucesor

            actualNodeId = actualNode.get('chordId', None)  # en el caso de q sea vacio o este muerto

            if actualNode:  # si es no vacio
                try:
                    with Pyro4.Proxy(actualNode['uri']) as remoteNode:
                        actualNodeSucessorId = remoteNode.sucessor['chordId']  # ese sucesor pudiera estar muerto!!!!!!
                except Pyro4.errors.CommunicationError: actualNode = {}
                # suceden cosas tan locas como q el sucesor del actualNode puede ser None puesto q se cayo y aun el
                # stabilize no ha terminado de actualizarlo
        return actualNode  # retorna el dict id, ip:port, uri, manager_uri

    def closest_preceding_finger(self, key: int) -> dict:
        interval = Interval(self.chordId, key, True, True)

        for index in range(self._functionBitNumber - 1, -1, -1):
            if len(self._fingerTable[index]['node']) > 0 and self._fingerTable[index]['node']['chordId'] in interval:
                return {'chordId': self._fingerTable[index]['node']['chordId'],
                        'address': self._fingerTable[index]['node']['address'],
                        'uri': self._fingerTable[index]['node']['uri'],
                        'manager_uri': self._fingerTable[index]['node']['manager_uri']}

        return {}  # solo pasa si no he actualizado mi tabla de finger o si la llave es = mi y yo soy el sucesor d todas
                # o si yo soy el sucesor de todas las llaves en ese caso se le pregunta a mi sucesor y funciona es asi
                # como se hace

    # region Este codigo va comentado pq es el de las inserciones aisladas
    # def update_others(self) -> None:
    #     for index in range(self._functionBitNumber):
    #         predecessor = self.find_predecessor(int((self.chordId - pow(2, index)) % self._pot))
    #         # todo esta resta es sobre el circulo de ids, verficar la operacion
    #
    #         with Pyro4.Proxy(predecessor['uri']) as remoteNode:
    #             remoteNode.update_finger_table({'chordId': self.chordId, 'address': self.address, 'uri': self.uri},
    #                                            index)
    #
    # def update_finger_table(self, node: dict, index: int) -> None:
    #     if node['chordId'] in Interval(self.chordId, self._fingerTable[index]['node']['chordId'], rexclude=True):
    #         self._fingerTable[index]['node'] = {'chordId': node['chordId'], 'address': node['address'],
    #                                             'uri': node['uri']}
    #
    #         predecessor = self.predecessor
    #
    #         with Pyro4.Proxy(predecessor['uri']) as remoteNode:
    #             remoteNode.update_finger_table(node, index)
    #
    # def init_finger_table(self, node:dict) -> None:
    #     with Pyro4.Proxy(node['uri']) as remoteNode:
    #         self._fingerTable[0]['node'] = remoteNode.find_sucessor(self._fingerTable[0]['start'])
    #
    #     # se inicializa el sucesor a partir de la 1ra entrada de la finger
    #     self.sucessor = {'chordId': self._fingerTable[0]['node']['chordId'],
    #                      'address': self._fingerTable[0]['node']['address'],
    #                      'uri': self._fingerTable[0]['node']['uri']}
    #
    #     with Pyro4.Proxy(self.sucessor['uri']) as remoteNode:
    #         self.predecessor = remoteNode.predecessor
    #         remoteNode.predecessor = {'chordId': self.chordId, 'address': self.address, 'uri': self.uri}
    #
    #     for index in range(self._functionBitNumber - 1):
    #         if self._fingerTable[index + 1]['start'] in Interval(self.chordId,
    #                                                              self._fingerTable[index]['node']['chordId'],
    #                                                              rexclude=True):
    #             self._fingerTable[index + 1]['node'] = {'chordId': self._fingerTable[index]['node']['chordId'],
    #                                                     'address': self._fingerTable[index]['node']['address'],
    #                                                     'uri': self._fingerTable[index]['node']['uri']}
    #         else:
    #             with Pyro4.Proxy(node['uri']) as remoteNode:
    #                 self._fingerTable[index + 1]['node'] = \
    #                     remoteNode.find_sucessor(self._fingerTable[index + 1]['start'])
    #
    # def join(self, node:dict) -> None:
    #     if node is not None:
    #         self.init_finger_table(node)
    #         self.update_others()
    #
    #         print('moviendo llaves usando algun mecanismo')
    #     else:
    #         for index in range(self._functionBitNumber):
    #             self._fingerTable[index]['node'] = {'chordId': self.chordId, 'address': self.address, 'uri': self.uri}
    #         self.predecessor = {'chordId': self.chordId, 'address': self.address, 'uri': self.uri}

    # endregion

    # region Codigo de inserciones concurrentes

    def join(self, node: dict) -> bool:
        if node:
            self.predecessor = None
            # seria el colmo q se cayera aqui!!!!!!!!!!!!!!!
            try:
                with Pyro4.Proxy(node['uri']) as remoteNode:
                    remoteNode._pyroTimeout = 7
                    self.sucessor = remoteNode.find_sucessor(self.chordId)  # pudieran darme un zombi!!!!!!!!!!!!!!

                print('mi sucesor para hacerle join es ' + str(self.sucessor))

                with Pyro4.Proxy(self.sucessor['uri']) as remoteNode:
                    remoteNode._pyroTimeout = 7
                    # hay q verificar q no sea un zombi!!!!!!!!!!!!!!!!!!
                    ancent_predecessor = remoteNode.predecessor
                    sucessor_list = remoteNode.get_sucessor_list

            except (Pyro4.errors.CommunicationError, Pyro4.errors.ConnectionClosedError, KeyError,
                    Pyro4.errors.TimeoutError,): return False
            # quizas sea buena idea pedirle la lista aqi y estabilizarla

            # region Codigo del movimiento de llaves de ray

            # movemos las llaves
            # conseguimos las llaves q estan en el intervalo (sucesor.anterior_predecesor, yo]
            # remoteManager: managers.DataManager
            # with Pyro4.Proxy(self.sucessor['manager_uri']) as remoteManager:
            #     try:
            #         item_interval: list = [
            #             item for item in remoteManager.get_range(start=ancent_predecessor['chordId'],
            #                                                          end=self.chordId, lexclude=True, rexclude=False)
            #         ]
            #         remoteManager.move_range(start=ancent_predecessor['chordId'], end=self.chordId, lexclude=True,
            #                                  rexclude=False, label='replicado')
            #
            #         # para los widgets
            #         for widget in item_interval:
            #             widget_data = remoteManager.get(id=widget[0], name=widget[1])
            #             self.data_manager.add(id=widget_data[0][0], name=widget_data[0][1], params=widget_data[0][2],
            #                                   state='propio', code=widget_data[1])
            #
            #     except (Pyro4.errors.CommunicationError, Pyro4.errors.TimeoutError,): return False
            #
            # # se las borramos al ultimo de la lista de sucesores de mi sucesor
            # if sucessor_list[-1]:
            #     with Pyro4.Proxy(sucessor_list[-1]['manager_uri']) as remoteManager:
            #         try:
            #             remoteManager.remove_range(start=ancent_predecessor['chordId'], end=self.chordId, lexclude=True,
            #                                  rexclude=False)
            #
            #         except (Pyro4.errors.TimeoutError, Pyro4.errors.CommunicationError,): return False

            # endregion

            # region nuevo codigo del movimiento de llaves

            try:
                with Pyro4.Proxy(self.sucessor['manager_uri']) as remoteManager:
                    remoteManager._pyroTimeout = 7
                    # todo estoy metiendo todos los codes en la ram puede dar overflow, se supone q itere y tire para el
                    # disk
                    item_interval = [
                                 item for item in remoteManager.get_interval(a=ancent_predecessor['chordId'],
                                             b=self.chordId, bajo_exclude=True, alto_exclude=False, widget=self.widget)
                             ]
                    remoteManager.change_labels_interval(a=ancent_predecessor['chordId'], b=self.chordId,
                                                         bajo_exclude=True, alto_exclude=False, estado_req='propio',
                                                         estado_final='replicado', widget=self.widget)

                if sucessor_list and sucessor_list[-1]:

                    with Pyro4.Proxy(sucessor_list[-1]['manager_uri']) as remote_last_manager:
                        remote_last_manager._pyroTimeout = 7

                        remote_last_manager.delete_interval(a=ancent_predecessor['chordId'], b=self.chordId,
                                bajo_exclude=True, alto_exclude=False, widget=self.widget,  estatus='replicado')

            except (Pyro4.errors.CommunicationError, Pyro4.errors.TimeoutError,): return False

            with Pyro4.Proxy(self.data_manager_uri) as my_dm:
                print('la lista de los elementos en el intervalo a conseguir es ' + str(item_interval))
                my_dm._pyroTimeout = 7
                for item in item_interval:
                    my_dm.append_item(item[0], item[4], widget=self.widget, params=item[3], estado='propio')

            # endregion
        else:
            # soy el unico nodo en la red, soy mi sucesor y mi predecesor
            for index in range(self._functionBitNumber):
                self._fingerTable[index]['node'] = {'chordId': self.chordId, 'address': self.address, 'uri': self.uri,
                                                    'manager_uri': self.data_manager_uri}
            # se hace en el notify, no importa
            self.predecessor = {'chordId': self.chordId, 'address': self.address, 'uri': self.uri,
                                'manager_uri': self.data_manager_uri}
            # soy mi predecesor y mi sucesor
            self.sucessor = {'chordId': self.chordId, 'address': self.address, 'uri': self.uri,
                             'manager_uri': self.data_manager_uri}

        return True

    def ping(self):
        return True

    def stabilize(self):
        # todo tengo q comprobar q este codigo no afecte los demas por estarse ejecutando concurrente
        # todo be careful with references in returning type of methods
        # region si mi sucesor se murio coge el primer vivo de la lista de sucesores
        sucessor_is_alive = False
        # se le hace ping a mi sucesor
        ancent_sucessor = self.sucessor

        with Pyro4.Proxy(self.sucessor['uri']) as remoteNode:
            try:
                remoteNode._pyroTimeout = 7
                sucessor_is_alive = remoteNode.ping()

            except (Pyro4.errors.CommunicationError, Pyro4.errors.TimeoutError,): pass  # esta muerto

        print(stabilize_title + 'haciendole ping a mi sucesor para ver si esta vivo: ' + str(sucessor_is_alive))
        # si no esta vivo, se selecciona el primero vivo de la lista de sucesores
        if not sucessor_is_alive:
            temp, sucessor_is_alive = utils.first_alive(self.sucessor_list)
            # se murio mi sucesor, puede haber qedado en otra red
            if self.sucessor not in self.node_list: self.node_list.add(self.sucessor)

            if sucessor_is_alive: self.sucessor = temp
            # todo esto es otro parche, implica q mi sucesor puede esta muerto pero nunca sera none, sucesor zombi

            print(stabilize_title + 'mi sucesor no esta vivo, ahora mi sucesor es: ')
            utils.print_node(self.sucessor)

        # endregion

        # region buscar el predecesor de mi sucesor, si esta vivo ver si pertenece a un intervalo mas carcano a mi
        # se le pide ahora el predecesor a mi sucesor, si no tengo sucesor va a lanzar excepcion
        sucessor_predecessor = None
        try:
            with Pyro4.Proxy(self.sucessor['uri']) as remoteNode:
                remoteNode._pyroTimeout = 7
                sucessor_predecessor = remoteNode.predecessor

            with Pyro4.Proxy(sucessor_predecessor['uri']) as remoteNode:
                remoteNode.ping()

        except (Pyro4.errors.CommunicationError, Pyro4.errors.TimeoutError,): sucessor_predecessor = None

        print(stabilize_title + 'el predecesor de mi sucesor es: ')
        utils.print_node(sucessor_predecessor)


        # se verifica q este vivo y en el intervalo en el q el pudiera ser mi nuevo sucesor
        if sucessor_predecessor and sucessor_predecessor['chordId'] in Interval(self.chordId, self.sucessor['chordId'],
                                                                                lexclude=True, rexclude=True):
            self.sucessor = sucessor_predecessor  # de ser asi es mi nuevo sucesor


            print(stabilize_title + 'ahora mi sucesor es, puesto q esta mas cerca a mi intervalo: ')
            utils.print_node(self.sucessor)
        # endregion
        # creo un comparador para el intervalo (sucessor, yo), a ese van a pertenecer todos mis sucesores potenciales
        interval_compare = utils.IntervalCompare(Interval(self.sucessor['chordId'], self.chordId, lexclude=True,
                                                          rexclude=True), self._functionBitNumber)


        print(stabilize_title + 'verificando q tengo sucesor para actualizar lista ')

        # region si tengo sucesor, se le pide su lista, se estabiliza, se eliminan los muertos
        if sucessor_is_alive:  # si tengo un sucesor, le pido su lista de sucesores, la estabilizo, hago la mia por
                                # la de el
            sucessor_list_of_sucessor = None
            sucessor_sucessor = None
            ancent_sucessor_list = self.sucessor_list  # nos qedamos con la anterior lista de sucesores para
                                # compararla con la nueva, de esta forma a los q ya no esten en la nueva se les quita
                                # las llaves y a los q estan se les da como replicado esto garantiza q siempre las
                                # llaves se encuentren replicadas en mi lista de sucesores

            with Pyro4.Proxy(self.sucessor['uri']) as remoteNode:
                try:
                    remoteNode._pyroTimeout = 7  # por si acaso
                    sucessor_list_of_sucessor = remoteNode.get_sucessor_list  # todo se supone q me devuelva una lista
                    sucessor_sucessor = remoteNode.sucessor                     # no una clase sucesorlist
                except (Pyro4.errors.CommunicationError, Pyro4.errors.TimeoutError,): return
            # si mi sucesor se cayo aqi no tiene sentido q actualice mi lista por la de el ni nada mas, retorno
            # inmediato para volver a ejecutar el stabilize y buscar en mi lista uno q este vivo

            self.sucessor_list = utils.Stabilizer.stabilize(sucessor_list_of_sucessor, interval_compare,
                                                            sucessor_sucessor)

            # region code de mantenimiento de llaves

            # pueden haber nodos muertos
            nodes_not_in_new_list = self._node_difference(ancent_sucessor_list, self.sucessor_list)
            # todo mi predecesor puede cambiar en medio de to-do este movimiento, lo mejor q se puede hacer es guardarlo
            # antes de entrar al stabilize, aunq se puede dejar q el nuevo predecesor arregle el lio
            self._remove_data_old_sucessors(nodes_not_in_new_list)
            self._remove_data_old_sucessor(ancent_sucessor)
            # cabe el problema de que se tenga mucha gente haciendo join y q no le de tiempo a alguno decirle al q
            # guardaba sus llaves anteriormente q las pase a replicadas o las borre esto es un caso en el q un nodo q
            # tenga llaves como propias aunq el no sea el q las guarde las va a seguir teniendo, qedan llaves basura
            # para evitar esto es necesario un proceso por detras q se encargue de borrar estas llaves

            # ademas de este problema esta tambien q solo le estoy borrando las llaves a los nodos q estaban en mi
            # anterior lista de sucesores q no estan en la actual, se las tengo q borrar a mi sucesor tambien, o sea, si
            # mi sucesor es distinto q mi anterior sucesor y no esta en la lista de sucesores tengo q eliminarle las
            # llaves

            # name hash state params code
            if self.predecessor and self.predecessor['chordId'] != self.chordId:
                with Pyro4.Proxy(self.data_manager_uri) as manager:
                    # es un problema tanto mantener el proxy abierto e iterar sobre el, de una forma si se cae se jodio la
                    # cosa de la otra se carga demasiadoa memoria, mejor iterar e ir guardando en el disco, para despues
                    # leer

                    for item in manager.get_interval(a=self.predecessor['chordId'], b=self.chordId, bajo_exclude=True,
                                                     alto_exclude=False, widget=self.widget):
                        # obligado ademas de esto es necesario un proceso por detras q se encargue de pasar a replicado o
                        # eliminar o pasar a replicadas aquellas llaves q se encuentran en otro intervalo q no sea mi
                        # predecesor y yo

                        for node in self.sucessor_list:
                            if node:
                                try:
                                    with Pyro4.Proxy(node['manager_uri']) as remoteManager:

                                        remoteManager.append_item(item[0], manager.get_item(item[0],
                                                                    widget=self.widget)[-1], widget=self.widget,
                                                                  params=item[3], estado='replicado')
                                        # todo el predecesor puede ser nil
                                        # todo esto lo estoy haciendo por cada nodo por cada item, cascara, modificar esto
                                        remoteManager.change_labels_interval(a=self.predecessor['chordId'],
                                            b=self.chordId, bajo_exclude=True, alto_exclude=False, estado_req='propio',
                                                                         estado_final='replicado', widget=self.widget)

                                except(Pyro4.errors.TimeoutError, Pyro4.errors.CommunicationError,): pass

                    # se las paso a replicado a mi nuevo sucesor si este no soy yo, otro parche
                    if self.sucessor['chordId'] != self.chordId:
                        for item in manager.get_interval(a=self.predecessor['chordId'], b=self.chordId,
                                                         bajo_exclude=True, alto_exclude=False, widget=self.widget):
                            try:
                                with Pyro4.Proxy(self.sucessor['manager_uri']) as remoteManager:
                                    remoteManager._pyroTimeout = 7

                                    remoteManager.append_item(item[0], manager.get_item(item[0],
                                                                widget=self.widget)[-1], widget=self.widget,
                                                              params=item[3], estado='replicado')

                                    remoteManager.change_labels_interval(a=self.predecessor['chordId'], b=self.chordId,
                                                     bajo_exclude=True, alto_exclude=False, estado_req='propio',
                                                                         estado_final='replicado', widget=self.widget)

                            except(Pyro4.errors.TimeoutError, Pyro4.errors.CommunicationError,): pass

            # endregion

            print(stabilize_title + 'se le pidio la lista de sucesores a mi sucesor')
            utils.print_sucessor_list(self.sucessor_list)

        deaths_number = utils.Stabilizer.deleteDeath(self.sucessor_list, interval_compare)
        # endregion

        print(stabilize_title + 'eliminando los muertos: ')
        # esto es completamente innecesario, si no tengo sucesor es pq todos estan muertos en mi lista, aqi puede ir un
        # if tengo sucesor, else es q no tengo pq se murio y no habia nadie vivo en mi lista, finally eliminar los
        # muertos, esto es para mayor belleza del codigo
        # region si todos estan muertos y no tengo sucesor, yo soy mi sucesor
        if not sucessor_is_alive and deaths_number == self.sucessor_list_size:
            # hacer broadcast a ver si hay otro nodo distinto de mi, si es asi el sera mi sucesor
            new_sucessor = self._get_a_chord()
            if new_sucessor:
                self.sucessor = new_sucessor
            else:
                self.sucessor = {'chordId': self.chordId, 'address': self.address, 'uri': self.uri,
                                 'manager_uri': self.data_manager_uri}
                # soy el sucesor de todas las llaves, ponerlo en mi finger, podria dar palo con el fix finger, van a
                # haber dos hilos escribiendo al mismo tiempo, hay q ponerle un lock a la finger cuando se vaya a
                # escribir
                # for index in range(self._functionBitNumber):
                #     self._fingerTable[index]['node'] = {'chordId': self.chordId, 'address': self.address,
                #                                         'uri': self.uri,
                #                                         'manager_uri': self.data_manager_uri}

                print(stabilize_title + 'ahora mi sucesor soy yo ')
        # endregion

        print(stabilize_title + 'el numero de muertos es: ' + str(deaths_number))
        print(stabilize_title + 'notificando de mi prescencia')
        print(stabilize_title + 'mi sucesor es: ')
        utils.print_node(self.sucessor)

        # esto puede ser un problema a la hora de la concurrencia puesto q se escribe una propiedad, mas nadie deberia
        # estarla usando, hasta q se termine de escribir, todo problema de concurrencia
        # en el caso de q se halla caido justo cuando voy a notificarle sencillamente paso, y espero a q se vuelva a
        # estabilizar, q se busq el primer vivo en la lista, etc
        try:
            with Pyro4.Proxy(self.sucessor['uri']) as remoteNode:
                remoteNode._pyroTimeout = 7
                # el unico palo q puede dar aqi es q este muerto mi sucesor
                utils.print_node({'chordId': self.chordId, 'address': self.address, 'uri': self.uri,
                                  'manager_uri': self.data_manager_uri})

                remoteNode.notify({'chordId': self.chordId, 'address': self.address, 'uri': self.uri,
                                   'manager_uri': self.data_manager_uri})
        except (Pyro4.errors.CommunicationError, Pyro4.errors.TimeoutError,): pass

    @Pyro4.oneway
    def notify(self, node: dict) -> None:
        isDeath = True

        print(notify_title + 'haciendole ping a mi predecesor a ver si esta vivo')

        # region Verificando si mi predecesor esta vivo

        # mi predecesor puede ser none, el primer notify q se me hace si no soy el primer nodo en la red
        if self.predecessor:
            with Pyro4.Proxy(self.predecessor['uri']) as remoteNode:
                remoteNode._pyroTimeout = 7
                try:
                    isDeath = not remoteNode.ping()
                # si esta muerto devuelve CommunicationError
                except (Pyro4.errors.CommunicationError, Pyro4.errors.TimeoutError,): pass
            # de otra forma solo puede devolver TimeoutError o ConnectionClosedError, u otra q el qiera

        # endregion

        print(notify_title + 'mi predecesor esta muerto: ' + str(isDeath))

        if self.predecessor is None or isDeath or node['chordId'] in \
                Interval(self.predecessor['chordId'], self.chordId, lexclude=True, rexclude=True):
            # si esta muerto agregarlo a la lista de nodos potenciales q pueden haber quedado en otro anillo
            if isDeath and self.predecessor and self.predecessor not in self.node_list:
                self.node_list.add(self.predecessor)

            self.predecessor = node
            if isDeath:
                # me hago cargo de los datos q estan entre mi nuevo predecesor y yo
                with Pyro4.Proxy(self.data_manager_uri) as data_manager:
                    data_manager.change_labels_interval(self.predecessor['chordId'], self.chordId,
                                                        estado_req='replicado', estado_final='propio',
                                                        bajo_exclude=True, alto_exclude=False, widget=self.widget)

        print(notify_title + 'mi predecesor ahora es: ')
        utils.print_node(self.predecessor)

    def fix_finger(self,a,b):  # cada 2s
        index = random.randint(a, b)

        print(fix_finger_title + 'el  indice es: ' + str(index))
        print(fix_finger_title + 'buscando la llave: ' + str(self._fingerTable[index]['start']))
        # esto puede ser un diccionario vacio
        nodeAtIndex = self.find_sucessor(self._fingerTable[index]['start'])


        if nodeAtIndex:
            print(fix_finger_title + 'el sucesor de {3} es chordId: {0}, address: {1}, uri: {2}'.format(
                nodeAtIndex['chordId'], nodeAtIndex['address'], nodeAtIndex['uri'], self._fingerTable[index]['start']))
        else:
            print(fix_finger_title + 'no pude encontrar el nodo en mi finger')

        # mi sucesor puede haberse muerto en ese caso esperar a q el stabilize solucione el problema, capturar si da
        # excepcion
        # aqi podria darse el caso de una redundancia en los llamados, seria un ciclo infinito si mi sucesor soy yo y no
        # encuentro al sucesor de la llave, me estaria llamando a mi mismo como sucesor constantemente
        if len(nodeAtIndex) == 0:

            print(fix_finger_title + 'no encuentro el sucesor de la llave en la tabla, se lo pregunto a mi sucesor')
            print(fix_finger_title + 'preguntandole a mi sucesor por: {0}'.format(self._fingerTable[index]['start']))


            # pero si mi sucesor soy yo mismo entonces el sucesor de la llave soy yo, otra modificacion del algoritmo
            # o sea, si yo no lo encuentro, le digo a mi sucesor q lo busq si mi sucesor no soy yo, si el no lo
            # encuentra tiene q devolverme a su sucesor para yo preguntarle y asi sucesivamente ir iterando, si por
            # casualidad yo soy el unico nodo en la red entonces soy el sucesor de esa llave si esta muerta, pero este
            # podria ser el caso de q yo me
            with Pyro4.Proxy(self.sucessor['uri']) as remoteNode:
                try:
                    remoteNode._pyroTimeout = 7
                    nodeAtIndex = remoteNode.find_sucessor(self._fingerTable[index]['start'])

                except (Pyro4.errors.CommunicationError, Pyro4.errors.TimeoutError,
                        Pyro4.errors.ConnectionClosedError,): return  # mi sucesor se cayo, tengo q esperar a q se
                # estabilize

            if nodeAtIndex:
                print(fix_finger_title + 'el sucesor de {3} es {0}, '
                                         'address: {1}, uri: {2}'.format(nodeAtIndex['chordId'], nodeAtIndex['address'],
                                                                nodeAtIndex['uri'], self._fingerTable[index]['start']))

        print(fix_finger_title + 'la finger table antes de modificarla era:')
        # utils.print_finger_table(self._fingerTable)
        # si no pudo actualizarce el nodo, este pudiera estar muerto, de ser asi, cuando se vaya a usar esta tabla, o se
        # le pregunta al sucesor, en el caso d q este muerto tambien se espera, o se espera a q se ponga bien la red
        # todo revisar bien pq pasa q hasta aqi puede llegar un diccionario vacio
        #utils.export_finger_table(self._fingerTable, 'antes de la modificacion', 'widgets')

        if nodeAtIndex: self._fingerTable[index]['node'] = nodeAtIndex

        print(fix_finger_title + 'la finger table despues de la modificacion es:')

        #utils.export_finger_table(self._fingerTable, 'despues de la modificacion', 'pages')
        # utils.print_finger_table(self._fingerTable)

    def _node_difference(self, first_nodes: list, second_nodes: list):

        difference = []
        is_in = False

        for old_widget in first_nodes:
            is_in = False
            for new_widget in second_nodes:
                if new_widget and old_widget and new_widget['chordId'] == old_widget['chordId']:
                    is_in = True
                    break

            if not is_in: difference.append(old_widget)

        return difference

    def _remove_data_old_sucessors(self, node_list: list):
        for node in node_list:
            if node:
                try:
                    with Pyro4.Proxy(node['manager_uri']) as remoteManager:
                        remoteManager._pyroTimeout = 7

                        remoteManager.delete_interval(a=self.predecessor['chordId'], b=self.chordId,
                                    bajo_exclude=True, alto_exclude=False, widget=self.widget, estatus='replicado')

                except (Pyro4.errors.CommunicationError, Pyro4.errors.TimeoutError,): pass

    def _remove_data_old_sucessor(self, ancent_sucessor):

        if ancent_sucessor['chordId'] != self.chordId and ancent_sucessor['chordId'] != self.sucessor['chordId'] and \
                ancent_sucessor not in self.sucessor_list:
            try:
                with Pyro4.Proxy(ancent_sucessor['manager_uri']) as remoteManager:
                    remoteManager._pyroTimeout = 7

                    remoteManager.delete_interval(a=self.predecessor['chordId'], b=self.chordId,
                                                  bajo_exclude=True, alto_exclude=False, widget=self.widget,
                                                  estatus='replicado')

            except (Pyro4.errors.CommunicationError, Pyro4.errors.TimeoutError,):
                pass

    def _get_a_chord(self):
        others_ns = ns_workers.NSFinder().get_others_ns()
        sucessor_uri = ''
        sucessor_manager_uri = ''
        new_sucessor = {}

        if others_ns:
            try:
                with Pyro4.Proxy(others_ns[0]) as remote_ns:
                    remote_ns._pyroTimeout = 7

                    if self.widget:  # puede ser q de lookup error pq intente hacer join a alguien q esta haciendo join
                        sucessor_uri = remote_ns.lookup('chord_widgets')
                    else:
                        sucessor_uri = remote_ns.lookup('chord_pages')
                    sucessor_manager_uri = remote_ns.lookup('data_manager')
            except (Pyro4.errors.CommunicationError, Pyro4.errors.TimeoutError,):
                return {}
            # aqi habria q intentar unir el anillo varias veces no hacer pass
            new_sucessor = {'chordId': int(hashlib.sha1(bytes(str(sucessor_uri).split('@')[1], 'utf-8')).hexdigest(),
                                           16),
                            'address': str(sucessor_uri).split('@')[1],
                            'uri': str(sucessor_uri),
                            'manager_uri': str(sucessor_manager_uri)}
        return new_sucessor

    def _set_finger(self, finger: dict):
        # todo anadir reentrant lock
        pass

    # endregion

    # region Codigo de los hilos, ejecutar periodicamente

    def fix_finger_forever(self):
        # todo poner una condicion con una variable semiglobal en el while para detener el hilo
        try:
            while True:
                div = 5 # tiene q ser un divior de 160
                salto = self._functionBitNumber / div
                bajo = 0
                alto = salto
                for _ in range(div):
                    self.fix_finger(bajo, alto - 1)
                    bajo = alto
                    alto += salto

                time.sleep(2.0)
        except KeyboardInterrupt: return

    def stabilize_forever(self):  # esto deberia hacerse con un decorador
        try:
            while True:
                self.stabilize()

                time.sleep(1.0)
        except KeyboardInterrupt: return

    def verify_topology_forever(self):
        try:
            while True:
                self.verify_topology()

                time.sleep(3.0)
        except KeyboardInterrupt:
            return

    # endregion

    # def count(self) -> int:
    #     previous: dict = {'chordId': self.chordId, 'address': self.address, 'uri': self.uri}
    #     next: dict
    #
    #     count: int = 0
    #     previous_is_alive: bool = True
    #     next_is_alive: bool

    #     while next.get('chordId', None) != self.chordId:  # None != int ???????????????????????????????
    #         next_is_alive = False
    #         while not next_is_alive:
    #             try:
    #                 with Pyro4.Proxy(previous['uri']) as remoteNode:
    #                     remoteNode._pyroTimeout = 3
    #
    #                     next = remoteNode.sucessor
    #
    #                     try:
    #                         with Pyro4.Proxy(next['uri']) as newRemoteNode:
    #                             newRemoteNode.ping()
    #                             next_is_alive = True
    #                             count += 1
    #                             previous = next
    #                     except (Pyro4.errors.CommunicationError, Pyro4.errors.TimeoutError,): pass
    #
    #             except (Pyro4.errors.TimeoutError, Pyro4.errors.CommunicationError,): return -1
    #             # se murieron dos consecutivos no se pudo contar hay q esperar a q se estabilice la red
    #
    #     return count

    # region Codigo de la verificacion de la particion de red, periodico
    # cada 5s, se puede hacer un metodo para la ejecucion en hilos q se le pase la funcion a ejecutar y cada cuanto
    # tiempo debe de ejecutar
    def verify_topology(self):

        for node in self.node_list:
            if node:
                try:
                    with Pyro4.Proxy(node['uri']) as remoteNode:
                        remoteNode._pyroTimeout = 7

                        my_sucessor = remoteNode.find_sucessor(self.chordId)

                        if my_sucessor and my_sucessor['chordId'] != self.chordId:
                            # seria bueno poder frezzear el stabilize en este punto
                            self.sucessor = my_sucessor  # esto es una mierda
                            # una vez q haga join deberia parar de hacerlo quizas borrando mi lista de nodos, puesto q
                            # podria estarlo haciendo una y otra vez sin haberme incorporado al anillo completamente
                            return

                except (Pyro4.errors.CommunicationError, Pyro4.errors.TimeoutError,):
                    pass
    # # to-do esto de la logica de trabajar con el proposer, los acepter y destruir el anillo deberia hacerlo otro objeto
    # def do_elections(self, key: list):
    #     propose = Proposer(key)
    #     propose.vote()
    #
    # def destroy_ring(self, key: list):  # esto debe tener otro nombre
    #     node: dict
    #     for node in key:
    #         if self.find_sucessor(node['chordId']) == node['chordId']:
    #             # es tu anillo destroit
    #             # elimina todos los datos
    #
    #             break

    # endregion

# todo invertir los try y los with
# todo ver lo del retry para la reconeccion si hay q hacer algo como eso
# hacer clases template, clases q tendran codigo ya escrito, try, except, whiles por ejemplo y se les pasara funciones
# q deberan ejecutar en distintas partes de ese codigo, una buena utilizacion en los try whit except y en la ejecucion
# forever de un hilo, sencillamente se le pasaria la funcion q debera ejecutar forever y el tiempo en el q debe hacer
# sleep asi como la condicion q debe chekear
# todo asegurarme q todo metodo remoto reciva y devuelva un nuevo objeto, no una referencia ni un proxy
# todo probar partes esopecificas, q se haga bien la tabla, el comparer del stabilizer, etc
# si me qedo solo en la red, o todos mis sucesores se mueren puede ser q sea el resultado de una destruccion, hay q
# hacer broadcast y volver a hacer join, no importa si es a otro nodo del pedazo del anillo q qede o a otro anillo,
# siempre el stabilize garantizara una correcta estructura del anillo eventualmente
if __name__ == '__main__':
    print('a')
    print(len({}))
    # todo si alguien se queda solo en la red pq se le murieron todos sus amigos, volver a hacer broadcast buscando la
    # red puesto q puede ser el caso q se halla empezado a destruir el anillo y el no halla tenido tiempo de buscar el
    # si la llave pertenece o no al anillo, por eso antes de empezar a romper el anillo y despues de buscar la llave
    # si la llave pertenece al anillo tuyo, se espera al menos 10s, tambien puede darse el caso de q se murieron k + 1
    # nodos consecutivos, en ese caso, si le hago join a cualquiera del anillo voy a encontrar nuevamente a mi sucesor
    # todo usar el multiprocesing en vez del threading, verificar q tenga acceso a las mismas variables
    # todo hacer los stubs
    # todo se recomienda hacer join varias veces si se es el unico nodo en la red, puesto q se puede haber hecho join a
    # todo un anillo q se este destruyendo, lo mismo si se es el unico nodo en la red y todos tu anillo se murio, puede
    # todo ser q se este en medio de una destruccion
    # una mejor idea es ponerle id a los anillos de esta forma uno se ahorra tiempo y se hace mas seguro, eso es tambien
    # un problema de concenso
# todo ver bien lo de los errores q pueden haber en la red
# el proxy es lazy no se crea hasta q se llama un metodo o propiedad
# aun falta revisar que el diccionario q me envia el objeto remoto sea accesible sin consultar al objeto remoto, es ver
# si eso funciona bien
# todo habilitar un log aparte del print en el debugger
# CommunicationError: no encontre el server al intentar conectar
# TimeoutError: estoy conectado con el server, se q existe, pero le hice una peticion y no responde
# ConnectionClosedError: el server me cerro la conexion