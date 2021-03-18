import Pyro4

from tools import ns_workers


class Lister():

    def __init__(self):
        pass

    @staticmethod
    def list_all(widgets) -> set:

        all_items = set()

        for ns in ns_workers.NSFinder.get_all_ns():
            dm_uri = ''
            try:
                with Pyro4.Proxy(ns) as remote_ns:
                    dm_uri = remote_ns.lookup('data_manager')

                with Pyro4.Proxy(dm_uri) as remote_dm:
                    owns = remote_dm.get_own(widget=widgets)  # retorna una lista de tuplas donde todos tienen estado
                                                                # propio
                    update = [ (x[0], x[3]) for x in owns if not (x[0], x[3]) in all_items]
                    all_items.update(set(update))

            except (Pyro4.errors.TimeoutError, Pyro4.errors.CommunicationError,): pass

        return all_items