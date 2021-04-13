import threading
import time

hilo = 0

def main(hilo):

    while True:
        print('soy el hilo ' + str(hilo))

        time.sleep(3.0)


