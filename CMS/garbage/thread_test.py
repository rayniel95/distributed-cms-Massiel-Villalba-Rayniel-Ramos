import time
from threading import Thread


class MyClass:

    def __init__(self):
        self.property = 1

    def modify_property(self):
        self.property += 1

    def thread_forever(self):
        times = 0
        while times < 4:
            self.modify_property()

            time.sleep(3.0)

            times += 1


def main():

    my_class = MyClass()

    my_thread = Thread(target=my_class.thread_forever, name='my_thread')
    my_thread.start()

    print(my_class.property)

    my_thread.join()

    print(my_class.property)

main()