class Accepter:

    def __init__(self):

        self.reset()
        self._uri = None

    @property
    def uri(self):
        return self._uri

    @uri.setter
    def uri(self, value):
        self._uri = value

    def prepare(self, ticket):

        if self.Tmax < ticket:
            self.Tmax = ticket
            return 'yes', self.Tstore, self.command, self.uri,

        return 'not', self.Tstore, self.command, self.uri,

    def propose(self, ticket, command):

        if ticket == self.Tmax:
            self.command = command
            self.Tstore = ticket

            return 'yes', self.uri,
        return 'not', self.uri,

    def reset(self):
        self.Tmax: int = 0  # Ticket más grande enviado
        self.command: list = []  # Comando guardado
        self.Tstore: int = 0  # Ticket con el que se guardó C

    def execute(self, command):
        # le dice a su chord q verifiq si es su anillo el q hay q romper
        self.reset()
