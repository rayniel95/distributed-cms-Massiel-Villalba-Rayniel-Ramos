import Pyro4

def main():

    my_uri = Pyro4.URI('PYRO:obj_89ee4b7da091491983afe9ff4b03f47d@192.168.43.95:37875')

    print(my_uri)

if __name__ == '__main__':
    main()