from proposer import Proposer


def main(args):
    Proposer(args.command, args.ticket).execute()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--command", type=str, help="command to execute")
    parser.add_argument("-t", "--ticket", default=0, type=int, help="Ticket for proposer")

    main(parser.parse_args())
