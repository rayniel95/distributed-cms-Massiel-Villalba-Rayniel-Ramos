import sqlite3, Pyro4, os

from math import fabs
 
@Pyro4.expose
class DataManager():
    def __init__(self,root_path):
        #def __init__(self,uri_widget_node,uri_page_node):
        #self.widget_node = Pyro4.Proxy(uri_widget_node)
        #self.page_node = Pyro4.Proxy(uri_page_node)
        self.db_url = root_path + "/data/db.sqlite3" 
        self.templates = root_path + '/templates/'
        self.cache_capacity = 4
        # todo no hacer una busqeda en la base de datos, sumar y restar en correspondencia
    
    def crear_archivo(self,name,code,widget=True):
        tipo = "widget" if widget else "page"
        #self.eliminar_archivo(name,widget=widget)

        # esto es mejor ponerlo en un contexto dentro de un with, en el caso de q de excepcion  se cierra
        # automaticamente

        file = open(self.templates + tipo + 's/' +name+'.html', 'w')
        file.write(code)
        file.close()
    def eliminar_archivo(self,name,widget=True):
        tipo = "widget" if widget else "page"
        try:
            os.remove(self.templates+tipo+'s/'+name+'.html')
            print("se ha eliminado el archivo "+name) 

        except:
            print("no se pudo eliminar el archivo "+name) 
    def leer_archivo(self,name,widget=True):
        url = "widget" if widget else "page"
        # todo mete todo esto en contextos
        file = open(self.templates+url+'s/'+name+'.html', 'r')
        code = file.read()
        file.close()
        return code 

    def append_tupla(self,tupla,widget=True):
        tipo = "widget" if widget else "page"
        conn = sqlite3.connect(self.db_url)
        cursor = conn.cursor()
        tupla_gen = "(?, ?, ?, ?, ?, ?)" if widget else "(?, ?, ?, ?, ?)"
        cursor.execute("insert into " + tipo + " values " + tupla_gen,tupla)  # todo mejor usar format_map, o ver los
        # paceholder de sqlite
        conn.commit()
        # todo cierra el cursor
        conn.close()

    def delete_tupla(self,name,widget=True):
        tipo = "widget" if widget else "page"
        conn = sqlite3.connect(self.db_url)
        cursor = conn.cursor()
        cursor.execute("delete from " + tipo + " where name = '" + name + "'")
        conn.commit()
        conn.close()

    def exists_tupla(self,name,widget=True):
        table = "widget" if widget else "page"
        where = " where name = '" + name+"'"
        result = self.query("name",table,where=where)
        return len(result)!=0

    # asumo q existe
    def get_item(self,name,widget=True):
        table = "widget" if widget else "page"
        code = self.leer_archivo(name,widget=widget)

        if(widget):
            where = " where name = '" + name+"'"
            s = self.query("params",table,where=where)
            params = s[0]
            return (params,code)
        else:
            return code
    # asumo q no existe
    # todo no eres nadie para estar asumiendo tanto, revisa primero si existe antes de agregar
    def append_item(self,name,code,widget = True,params=None,cache=False,propio=False,replicado=False):
        self.crear_archivo(name,code,widget=widget)
        #sha1_hash = hash(sha1(name).digest())
        tipo = 'widget' if widget else 'page'
        sha1_hash = fabs(hash(name))
        # todo poner esto en hexdigest q te va a devolver un string en hexadecimal y despues lo pasas a entero en base
        # 16
        # el hash a veces da negativo, no le pongo modulo xq no se si 2 hash pueden tener el mismo abs
        tupla = (name,sha1_hash,cache,propio,replicado,params) if widget else (name,sha1_hash, cache,propio,replicado)

        if(cache):
            where = " where cache = 1 and replicado=0 and propio=0"
            query = self.query("name", tipo, where=where)
            if len(query)==self.cache_capacity:
                print("cache llena ... eliminando item")
                name = query[0][0]
                self.delete_item(name,widget=widget)

        self.append_tupla(tupla,widget=widget)
            
    def delete_item(self, name, widget = True):
        self.eliminar_archivo(name,widget=widget)
        self.delete_tupla(name,widget=widget)

    def delete_interval(self,a,b,bajo = True, alto = True, widget = True):
        query = self.interval(a,b,bajo=bajo,alto=alto,widget=widget,columns="name")  # todo trabajar con el intervalo
        for x in query:
            self.delete_item(x[0],widget = widget)

    def get_interval(self,a,b,bajo = True, alto = True, widget = True):
        query = self.interval(a,b,bajo=bajo,alto=alto,widget=widget,columns="name")
        sol = []
        for x in query:
            sol.append(self.get_item(x[0],widget = widget))  # todo hacer un iterador
        return sol

    def empty_interval(self,a,b,bajo = True, alto = True, widget = True):
        query = self.interval(a,b,bajo=bajo,alto=alto,widget=widget)
        return len(query)==0

    def change_labels_interval(self,a,b,bajo = True, alto = True, widget=True, cache=True,replicado=True,propio=True,
                               modificar_cache=True,modificar_propio=True,modificar_replicado=True,condition =None):
        tabla = 'widget' if widget else 'page'
        iz = a-1 if bajo else a
        der = b+1 if alto else b
        where = " where hash>"+str(iz)+" and hash<"+str(der)
        if(condition):
            where += " and "+condition
        
        setear = []  # todo esto es horroooooooor
        if(modificar_cache):
            setear.append("cache="+str(cache))
        if(modificar_replicado):
            setear.append("replicado="+str(replicado))
        if(modificar_propio):
            setear.append("propio="+str(propio))

        setear = setear[0] if len(setear)==1 else setear[0]+','+setear[1] if len(setear)==2 else setear[0]+','+setear[1]+','+setear[2]         

        conn = sqlite3.connect(self.db_url)
        cursor = conn.cursor()
        result = cursor.execute("update "+tabla+" set " + setear +" "+ where)
        result = result.fetchall()
        conn.commit()
        conn.close()
        self.limpiar(widget=widget,where="cache=0 and replicado=0 and propio=0")

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
        conn.close()
        return result
# todo cascara
    def interval(self,a,b,bajo = True, alto = True, widget = True, columns = "*"):
        tabla = 'widget' if widget else 'page'
        iz = a-1 if bajo else a
        der = b+1 if alto else b
        where = " where hash>"+str(iz)+" and hash<"+str(der)

        return self.query(columns,tabla,where=where)