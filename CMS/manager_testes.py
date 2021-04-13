from tools.managers import DataManager 
import sqlite3, os
from random import randint
import sys
           


propertys = ["color","texto1","texto2","fuente","padding","lista"]
root = sys.path[0]
print(root)
manager = DataManager(root)

def leer_data(widget=True):
    conn = sqlite3.connect(root + "/data/db.sqlite3")
    cursor = conn.cursor()

    print("WIDGETS") if widget else print("PAGES")
    tabla = "widget" if widget else "page"
    result = cursor.execute("select * from "+tabla+" order by name")
    for x in result.fetchall():
        print(x) if widget else print(x[0: 3])

    cursor.close()
    conn.close()


def rellenar(code, cantidad, widget=True):
    name = "p"
    #append_item(self,name,code,widget = True,params=None,estado="")
    for x in range(0,cantidad):
        estado = ramdom_labels()
        params = None
        nombre = str(name+str(x))
        manager.append_item(nombre,(code+"<br>")*x,widget=widget,params=params,estado=estado)

def ramdom_labels():
    labels = ["cache","propio","replicado"]
    index = randint(0,len(labels)-1)
    return labels[index]

def borrar_todo():
    manager.limpiar()
    manager.limpiar(widget=False)
def interval(a,b,widget=True):
    #get_interval(self,a,b,bajo = True, alto = True, widget = True):
    sol = manager.get_interval(a,b,widget=widget)
    print("INTERVAL")
    for x in sol:
        print("name "+x[0]+" hash "+str(int(x[1],16)))

#def delete_interval(self,a,b,bajo = True, alto = True, widget = True):
def delete_interval():
    sol = manager.delete_interval(0,700000000000000000000000,widget=False)
def change(a,b,req,final,widget=True):
    # change_labels_interval(a,b,estado_req, estado_final, widget=True):
    print("antes de cambiar labels")
    interval(a,b,widget=widget)
    manager.change_labels_interval(a,b,req,final,widget=widget)
    print("despues de cambiar labels")
    interval(a,b)



print("LEYENDO DATA")
leer_data(widget=False)
leer_data()
#borrar_todo()
#borrar_todo()
#leer_data(widget=False)
#leer_data()
#interval(0,pow(2,159),widget=False)