import sqlite3
import sys
import time
import threading
import multiprocessing

def main():
    print('{path_root}/{name}'.format_map({'path_root': sys.path[0], 'name': 'db.sqlite3'}))


    print('inserte')
    time.sleep(9.0)
    print('termine de esperar')

    conn2 = sqlite3.connect('{path_root}/{name}'.format_map({'path_root': sys.path[0], 'name': 'db.sqlite3'}),
                            timeout=5.0, check_same_thread=True)

    conn2.interrupt()
    print('abri la conexion')
    conn2.cursor().execute('update page set name="ray" where estado="estado"')

def hilo1():
    conn = sqlite3.connect('{path_root}/{name}'.format_map({'path_root': sys.path[0], 'name': 'db.sqlite3'}))
    cursor = conn.cursor()

    cursor.execute('insert into page values ("caso", "11212323", "estado", "params")')

    conn.commit()
    cursor.close()
    conn.close()


def hilo2():
    time.sleep(3.0)
    conn = sqlite3.connect('{path_root}/{name}'.format_map({'path_root': sys.path[0], 'name': 'db.sqlite3'}))
    cursor = conn.cursor()

    try:
        cursor.execute('insert into page values ("caso", "11212323", "estado", "params")')
    except: print('excepcion')

    conn.commit()
    cursor.close()
    conn.close()

def hilo3():
    time.sleep(10.0)

    conn = sqlite3.connect('{path_root}/{name}'.format_map({'path_root': sys.path[0], 'name': 'db.sqlite3'}))
    cursor = conn.cursor()

    cursor.execute('update page set estado="coxo" where name="caso"')

    conn.commit()
    cursor.close()
    conn.close()


if __name__ == '__main__':
    conn = sqlite3.connect('{path_root}/{name}'.format_map({'path_root': sys.path[0], 'name': 'db.sqlite3'}))
    cursor = conn.cursor()

    cursor.execute('delete from page where name="caso"')

    conn.commit()
    cursor.close()
    conn.close()

    multiprocessing.Process(target=hilo1).start()

    multiprocessing.Process(target=hilo2).start()

    multiprocessing.Process(target=hilo3).start()

