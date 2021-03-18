import threading
import time

class Prova():

    def __init__(self):
        self.condition = True

    def prova(self):

        while self.condition:
            print('prova')

def main():

    prova1 = Prova()

    threading.Thread(target=prova1.prova).start()

    time.sleep(5.0)

    prova1.condition = False

main()

