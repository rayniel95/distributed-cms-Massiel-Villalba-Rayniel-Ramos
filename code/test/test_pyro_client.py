import Pyro4
from tools import ns_workers

def main():
    #own_ns = ns_workers.NSFinder().get_own_ns()

    tester_uri = ''
    #
    # with Pyro4.Proxy(own_ns) as remoteNs:
    #     tester_uri = remoteNs.lookup('tester')

    with Pyro4.Proxy('PYRO:algo@192.168.43.234:35819') as remote_tester:
        print(remote_tester.hello())


if __name__ == '__main__':
    main()