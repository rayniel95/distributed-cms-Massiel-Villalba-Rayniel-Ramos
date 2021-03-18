import Pyro4

from accepter import Accepter


def main(args):
    
    AccepterE = Pyro4.expose(Accepter)

    with Pyro4.Daemon() as daemon:

        ns = Pyro4.locateNS(host="localhost", port=9090)

        uri = daemon.register(AccepterE())
        ns.register(args.name, uri, metadata={"accepter"})  # add parameters

        daemon.requestLoop()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--name", help="Name for given accepter")

    main(parser.parse_args())
