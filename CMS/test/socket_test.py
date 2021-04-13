import socket

from Pyro4 import socketutil

# para hacer broadcast con pyro y obtener todos los name server en una red local
def main():
    server = socketutil.createBroadcastSocket(('127.0.0.1', 9005), timeout=1)

    client1 = socketutil.createBroadcastSocket()
    client2 = socketutil.createBroadcastSocket()

    client1.sendto(b'algo', 0, ('0.0.0.0', 9005))
    client2.sendto(b'otro algo', 0, ('0.0.0.0', 9005))

    try:
        client1.shutdown(socket.SHUT_RDWR)
        client2.shutdown(socket.SHUT_RDWR)
    except: pass

    client1.close()
    client2.close()

    try:
        data, addr = server.recvfrom(100)
        print(data)
        data, addr = server.recvfrom(100)
        print(data)
        data, addr = server.recv(100, 16)
        print(data)
    except:
        print('excepcion')

    try:
        server.shutdown(socket.SHUT_RDWR)
    except: pass

    server.close()


if __name__ == '__main__':
    main()