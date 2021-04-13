import sqlite3, Pyro4, os
from Chord.chord.interval import Interval
from hashlib import sha1
from random import randint
from tools.cache_checker import CacheCheckerPages
from threading import Thread


@Pyro4.expose
class DataManager():

    def __init__(self, root_path):
        self.db_url = root_path + "/data/db.sqlite3"
        self.templates = root_path + '/data/'
        self.cache_disponible = 10
        self.checker_list = {}
        self._timeout = 10
        self.root_path = root_path

    def crear_archivo(self, name, code, widget=True):
        tipo = "widget" if widget else "page"

        try:
            with open(self.templates + tipo + 's/' + name + '.html', 'w') as file:
                file.write(code)

        except:
            print('ocurrio un error al crear el archivo')

    def eliminar_archivo(self, name, widget=True):
        tipo = "widget" if widget else "page"
        try:
            os.remove(self.templates + tipo + 's/' + name + '.html')
            print("se ha eliminado el archivo " + name)

        except:
            print("el archivo " + name + ".html no existe")

    def leer_archivo(self, name, widget=True):
        url = "widget" if widget else "page"
        code = None

        try:
            with open(self.templates + url + 's/' + name + '.html', 'r') as file:
                code = file.read()

        except:
            print("el archivo " + name + ".html no existe")

        return code

    # def get_row(self, name, widget=True):
    #     tipo = "widget" if widget else "page"
    #     conn = sqlite3.connect(self.db_url,timeout=self._timeout)
    #     cursor = conn.cursor()
    #
    #     row = cursor.execute('select * from :table where name=:name', {'table': tipo, 'name': name})
    #
    #     cursor.close()
    #     conn.close()
    #
    #     return row

    def get_own(self, widget=True):
        tipo = "widget" if widget else "page"

        return self.query("*", tipo, " where estado='propio'")

    def append_tupla(self, tupla, widget=True):
        tipo = "widget" if widget else "page"

        try:
            with sqlite3.connect(self.db_url, timeout=self._timeout) as conn:
                cursor = conn.cursor()

                cursor.execute("insert into " + tipo + " values (?, ?, ?, ?)", tupla)

                cursor.close()
        except:
            print("ya la tupla " + str(tupla) + " existe")

    def delete_tupla(self, name, widget=True):
        tipo = "widget" if widget else "page"

        with sqlite3.connect(self.db_url, timeout=self._timeout) as conn:
            cursor = conn.cursor()
            # esto puede ser un error puesto q se ejecuta el metodo exist_tupla con la conexion abierta
            if self.exists_tupla(name, widget):
                cursor.execute("delete from " + tipo + " where name = '" + name + "'")

            cursor.close()

    def update_tupla(self, name, params):

        with sqlite3.connect(self.db_url, timeout=self._timeout) as conn:
            cursor = conn.cursor()

            cursor.execute("update page set params='" + params +"' where name='"+name+"'")

            cursor.close()

    def exists_tupla(self, name, widget=True):
        table = "widget" if widget else "page"
        where = " where name = '" + name + "'"
        result = self.query("name", table, where=where)

        return len(result) != 0


    def get_item(self, name, widget=True):
        print("buscar " + name)

        if self.exists_tupla(name, widget=widget):

            table = "widget" if widget else "page"
            where = " where name = '" + name + "'"
            params = self.query("params", table, where=where)[0][0]  # aqi se indexa pq query hace fetchall
            code = self.leer_archivo(name, widget=widget)

            return (params, code)

        return (None, None)

    # todo recordar q masiel le cambio el orden a los parametros, pq hace esas cosas???????????????????????????????
    @Pyro4.oneway
    def append_item(self, name, code, widget=True, params="", estado=""):
        tipo = 'widget' if widget else 'page'

        if self.exists_tupla(name, widget=widget):
            if widget:
                print("ya existe un widget con ese nombre en la bd")
                return False

            else:
                self.crear_archivo(name, code, widget=widget)
                self.update_tupla(name, params)
                return True

        print("no existe")
        # si ya esta se sobrescribe, si no, se crea
        self.crear_archivo(name, code, widget=widget)
        sha1_hash = sha1(bytes(name, 'utf-8')).hexdigest()

        tupla = (name, sha1_hash, estado, params)

        if estado == "cache":
            self.cache_disponible -= 1
            if self.cache_disponible < 0:
                where = " where estado='cache'"
                query = self.query("name", tipo, where=where)
                random = randint(0, len(query) - 1)
                self.delete_item(query[random][0], widget=widget)
                self.cache_disponible += 1
        # esto es un error, un hilo vino, pregunta si existe la tupla, le dicen q no, va a insertar, devuelve el control
        # del gil antes de hacerlo, biene otro, pregunta si la tupla existe, le dicen q no, devuelve el control del gil
        # al anterior, el anterior inserta pasa el control al segundo, el segundo inserta, excepcion, las operaciones
        # sobre la base de datos tienen q ser atomicas, o sea, mientras se este ejecutando por un hilo varias
        # operaciones, esta debe permanecer bloqueada, revisar bien estos casos
        self.append_tupla(tupla, widget=widget)

        if not (self.checker_list.__contains__(name)) and estado == "cache":
            self.checker_list[name] = CacheCheckerPages(name, params)

            Thread(target=self.checker_list[name].ask_for_params_change).start()

        return True

    def delete_item(self, name, widget=True):
        table = 'widget' if widget else 'page'

        estado = self.query("estado", table, where=" where name='" + name + "'")[0][0]

        if estado == "cache" and self.checker_list.__contains__(name):
            self.checker_list[name].condition_continue = False
            del self.checker_list[name]

        self.delete_tupla(name, widget=widget)
        self.eliminar_archivo(name, widget=widget)

    def interval(self, a, b, bajo_exclude=False, alto_exclude=False, widget=True, where=""):
        intervalo = Interval(a, b, lexclude=bajo_exclude, rexclude=alto_exclude)
        print("el intervalo es " + str(intervalo))
        tabla = 'widget' if widget else 'page'
        todo = self.query("*", tabla, where=where)  # lista de tuplas donde el estado es replicado
        sol = []
        for x in todo:
            hash = int(x[1], 16)
            if (intervalo.__contains__(hash)):
                sol.append(x)
        return sol

    def delete_interval(self, a, b, bajo_exclude=False, alto_exclude=False, widget=True, estatus=""):
        tupla = tuple(estatus.split())

        len_tupla = len(tupla)
        tupla = str(tupla)

        if len_tupla < 2:
            temp = ''
            for char in tupla:
                if char != ',': temp += char

            tupla = temp

        where = " where estado in " + tupla
        query = self.interval(a, b, bajo_exclude=bajo_exclude, alto_exclude=alto_exclude, widget=widget, where=where)
        for x in query:
            self.delete_item(x[0], widget=widget)

    def get_interval(self, a, b, bajo_exclude=False, alto_exclude=False, widget=True):
        query = self.interval(a, b, bajo_exclude=bajo_exclude, alto_exclude=alto_exclude, widget=widget)
        for x in query:
            code = self.leer_archivo(x[0], widget=widget)
            yield x + (code,)

    def empty_interval(self, a, b, bajo_exclude=False, alto_exclude=False, widget=True):
        query = self.interval(a, b, bajo_exclude=bajo_exclude, alto_exclude=alto_exclude, widget=widget)
        return len(query) == 0

    @Pyro4.oneway
    def change_labels_interval(self, a, b, estado_req, estado_final, bajo_exclude=False, alto_exclude=False,
                               widget=True):
        tabla = 'widget' if widget else 'page'
        where = " where estado='" + str(estado_req) + "'"
        cambiar = self.interval(a, b, bajo_exclude=bajo_exclude, alto_exclude=alto_exclude, widget=widget, where=where)
        # devuelve una lista de tuplas
        to_change = []
        for x in cambiar:
            to_change.append(x[0])

        len_to_change = len(to_change)
        to_change = str(tuple(to_change))

        if len_to_change < 2:
            temp = ''
            for char in to_change:
                if char != ',': temp += char

            to_change = temp

        where = " where name in " + to_change


        with sqlite3.connect(self.db_url,timeout=self._timeout) as conn:
            cursor = conn.cursor()
            cursor.execute("update " + tabla + " set estado='" + estado_final + "' " + where)

            cursor.close()


    def limpiar(self, widget=True, where=""):
        table = "widget" if widget else "page"
        query = self.query("name", table, where=where)
        for x in query:
            self.delete_item(x[0], widget=widget)

    def query(self, query_str, table, where=""):
        result = None

        with sqlite3.connect(self.db_url,timeout=self._timeout) as conn:
            cursor = conn.cursor()
            result = cursor.execute("select " + query_str + " from " + table + " " + where)
            result = result.fetchall()

            cursor.close()

        return result
