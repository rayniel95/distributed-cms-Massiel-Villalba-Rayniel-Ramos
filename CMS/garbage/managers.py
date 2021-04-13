import Pyro4
import os
import sqlite3
from hashlib import sha1
from random import randint

from Chord.chord.interval import Interval


@Pyro4.expose
class DataManager():
    def __init__(self,root_path):
        #def __init__(self,uri_widget_node,uri_page_node):
        #self.widget_node = Pyro4.Proxy(uri_widget_node)
        #self.page_node = Pyro4.Proxy(uri_page_node)
        self.db_url = root_path + "/data/db.sqlite3" 
        self.templates = root_path + '/templates/'
        self.cache_disponible = 4

    def crear_archivo(self,name,code,widget=True):
        tipo = "widget" if widget else "page"
        #self.eliminar_archivo(name,widget=widget)
        file = open(self.templates + tipo + 's/' +name+'.html', 'w') 
        file.write(code)
        file.close()

    def eliminar_archivo(self,name,widget=True):
        tipo = "widget" if widget else "page"
        try:
            os.remove(self.templates+tipo+'s/'+name+'.html')
            print("se ha eliminado el archivo "+name) 

        except:
            print("el archivo "+name+".html no existe") 

    def leer_archivo(self,name,widget=True):
        url = "widget" if widget else "page"

        try:
            file = open(self.templates+url+'s/'+name+'.html', 'r')
        except:
            raise IOError("el archivo "+name+".html no existe")

        code = file.read()
        file.close()
        return code 

    def append_tupla(self,tupla,widget=True):
        tipo = "widget" if widget else "page"
        conn = sqlite3.connect(self.db_url)
        cursor = conn.cursor()

        try:
            cursor.execute("insert into " + tipo + " values (?, ?, ?, ?)", tupla)
        except:
            print("ya la tupla " + str(tupla) + " existe")

        conn.commit()
        cursor.close()
        conn.close()

    def delete_tupla(self, name, widget=True):
        tipo = "widget" if widget else "page"
        conn = sqlite3.connect(self.db_url)
        cursor = conn.cursor()

        if self.exists_tupla(name, widget):
            cursor.execute("delete from " + tipo + " where name = '" + name + "'")

        conn.commit()
        cursor.close()
        conn.close()

    def exists_tupla(self, name, widget=True):
        table = "widget" if widget else "page"
        where = " where name = '" + name +"'"

        result = self.query("name", table, where=where)

        return len(result) != 0

    # asumo q no existe
    # widget = (name,hash,estado,params)
    def append_item(self, name, code, widget=True, params="", estado=""):
        tipo = 'widget' if widget else 'page'

        if self.exists_tupla(name, widget=widget):
            print("ya existe un item tipo "+ tipo +" con ese nombre en la bd")
            return

        self.crear_archivo(name, code, widget=widget)
        print("name "+name)
        sha1_hash = sha1(bytes(name, 'utf-8')).hexdigest()

        tupla = (name, sha1_hash, estado, params)
        
        if estado == "cache":
            self.cache_disponible -= 1
            if self.cache_disponible <= 0:
                where = " where estado='cache'"
                query = self.query("name", tipo, where=where)
                random = randint(0, len(query) - 1)
                self.delete_item(query[random][0], widget=widget)
                self.cache_disponible += 1

        self.append_tupla(tupla, widget=widget)
            
    def delete_item(self, name, widget = True):
        self.eliminar_archivo(name, widget=widget)
        self.delete_tupla(name, widget=widget)

    def interval(self, a, b, bajo_exclude=False, alto_exclude=False, widget=True, where=""):
        intervalo = Interval(a, b, lexclude=bajo_exclude, rexclude=alto_exclude)
        print("el intervalo es "+str(intervalo))
        tabla = 'widget' if widget else 'page'
        todo = self.query("*", tabla, where=where)
        sol = []
        for x in todo:
            hash = int(x[1], 16)
            s = "para hash="+str(hash)
            if(intervalo.__contains__(hash)):
                s += "  "+str(True)
                sol.append(x)
            print(s)
        return sol

    def delete_interval(self, a, b, bajo_exclude=False, alto_exclude=False, widget=True, estatus=""):
        tupla = str(tuple(estatus.split()))
        where = " where estado in " + tupla
        query = self.interval(a, b, bajo_exclude=bajo_exclude, alto_exclude=alto_exclude, widget=widget, where=where)

        for x in query:
            self.delete_item(x[0], widget=widget)

    def get_interval(self,a,b,bajo_exclude = False, alto_exclude = False, widget = True):
        query = self.interval(a,b,bajo_exclude = bajo_exclude, alto_exclude = alto_exclude,widget=widget)
        for x in query:
            code = self.leer_archivo(x[0], widget=widget)
            yield x + (code)

    def empty_interval(self,a,b,bajo_exclude = False, alto_exclude = False, widget = True):
        query = self.interval(a,b,bajo_exclude = bajo_exclude, alto_exclude = alto_exclude,widget=widget)
        return len(query)==0

    def change_labels_interval(self,a,b,estado_req, estado_final, bajo_exclude=False, alto_exclude=False,
                               widget=True):
        tabla = 'widget' if widget else 'page'
        where = " where estado='"+str(estado_req)+"'"
        cambiar = self.interval(a, b, bajo_exclude=bajo_exclude, alto_exclude=alto_exclude, widget=widget, where=where)

        tupla_in = "("
        if len(cambiar) > 0:
            tupla_in+= "'"+cambiar[0][0]+"'"
            cambiar=cambiar[1:len(cambiar)]
            for x in cambiar:
                tupla_in += ", '"+x[0]+"'"
            tupla_in+=")"

            print("tupla  fea  "+tupla_in)

            where = " where name in " + tupla_in 
            conn = sqlite3.connect(self.db_url)
            cursor = conn.cursor()
            result = cursor.execute("update "+tabla+" set estado='" + estado_final +"' "+ where)
            result = result.fetchall()
            conn.commit()
            cursor.close()
            conn.close()

    def limpiar(self,widget=True,where=""):
        table = "widget" if widget else "page"
        query = self.query("name",table,where=where)

        for x in query:
            self.delete_item(x[0],widget=widget)

    def query(self,query_str,table,where=""):
        conn = sqlite3.connect(self.db_url)
        cursor = conn.cursor()

        result = cursor.execute("select "+query_str+" from " + table +" "+ where)
        result = result.fetchall()

        conn.commit()

        cursor.close()
        conn.close()

        return result