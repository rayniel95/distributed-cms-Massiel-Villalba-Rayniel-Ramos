


class ContextTest():

    def __init__(self):
        pass

    def __enter__(self):
        print('entre')

    def __exit__(self, exc_type, exc_val, exc_tb):
        print('sali')


def main():

    with ContextTest() as context:
        try:
            raise Exception('problem')

        except: return

if __name__ == '__main__':
    main()