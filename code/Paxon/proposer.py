import random
import Pyro4

from tools import ns_workers


class Proposer:

    def __init__(self, command: list):
        """

        :param command: es una lista donde estaran los 4 nodos consecutivos, de los cuales selecciono el
                        primero para representar la lista, es normal q varios proposer decidan enviar diferentes
                        solicitudes q representen el mismo anillo, al final solo se escojera 1 y seran ellos los q
                        comiencen a romper el anillo
        :param ticket: deberia ser un randomint
        """
        self.command: list = command
        self.reset()


    def reset(self):
        self.accepters: list = []
        self.result_propose: list = []
        self.result_prepare: list = []
        self.ticket = 0

    def _all_accepters(self):

        remotes_ns = ns_workers.NSFinder.get_all_ns()

        for uri in remotes_ns:
            try:
                with Pyro4.Proxy(uri) as remote_ns:
                    remote_ns._pyroHmacKey = None
                    remote_ns._pyroTimeout = 3

                    accepter_uri = remote_ns.lookup('accepter')

                    if accepter_uri not in self.accepters: self.accepters.append(accepter_uri)

            except (Pyro4.errors.CommunicationError, Pyro4.errors.TimeoutErrors,): pass

    def do_execute(self):
        if self.count_accepted(self.result_propose) > len(self.result_propose) / 2:
            for item in self.result_propose:
                if item[0] == 'yes':
                    try:
                        with Pyro4.Proxy(item[1]) as remoteNode:
                            remoteNode.execute(self.command)
                    except (Pyro4.errors.TimeoutErrors, Pyro4.errors.CommunicationError,): pass

        else:
            self.result_propose = []
            self.result_prepare = []

            self.do_prepare()
    # estos metodos van protected
    def do_prepare(self):
        self.ticket += random.randint(1, 6)

        for acepter_uri in self.accepters:
            try:
                with Pyro4.Proxy(acepter_uri) as remoteNode:
                    remoteNode._pyroTimeout = 3
                    self.result_prepare.append(remoteNode.prepare(self.ticket))

            except (Pyro4.errors.CommunicationError, Pyro4.errors.TimeoutErrors,): pass

        self.do_propose()

    def vote(self):
        self._all_accepters()
        self.do_prepare()

    @staticmethod
    def count_accepted(result: list) -> int:
        count: int = 0
        item: tuple
        for item in result:
            if item[0] == 'yes': count += 1

        return count

    def do_propose(self):
        # asegurar q la mayoria responde ok, se cogen las respuestas de todos, los q aceptan y los q no aceptan pq lo
        # hacen, se cuentan los grupos, se coge la mayoria, si la mayoria no responde ok volver a do_prepare

        if self.count_accepted(self.result_prepare) > len(self.result_prepare) / 2:  # todo ver q esto funcione para
            # longitud impar
            # seleccionar el (Tstore, C) con mayor Tstore

            greather: int = 0
            command: list = []
            for item in self.result_prepare:
                if item[1] > greather:
                    greather = item[1]
                    command = item[2]

            if greather > 0:
                self.command = command

            for item in self.result_prepare:
                if item[0] == 'yes':
                    try:
                        with Pyro4.Proxy(item[3]) as remoteNode:
                            remoteNode._pyroTimeout = 3

                            self.result_propose.append(remoteNode.propose(self.ticket, self.command))
                    except (Pyro4.errors.CommunicationError, Pyro4.errors.TimeoutErrors,): pass

        else:
            self.result_prepare = []  # no tendre mi comando inicial pero la idea es llegar a un concenso, no q mi
            # commando sea escogido
            self.do_prepare()