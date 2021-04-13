import Pyro4
from flask import render_template_string, render_template
#from tools.managers import DataManager
from hashlib import sha1


my_chord_widget = 2
my_chord_page = 7
mi_uri = "PYRO:obj_ca0723fa619a4fb49fbd4bc7fdf1e497@localhost:9005"

def my_hash(name):
    return int(sha1(bytes(name, 'utf-8')).hexdigest(),16)

def armar_pagina(name,header,nav,section,aside,footer):
    todo = [header,nav,section,aside,footer]
    for i in range(0,len(todo)):
        todo[i] = crear_section(todo[i])
        if todo[i]==None:
            return None
    dic = {'header':todo[0], 'nav':todo[1],'section':todo[2],'aside':todo[3],'footer':todo[4]}
    return render_template('base_pages.html',**dic)

def crear_section(list_widget:list):
    section_code = ""
    for x in list_widget:
        if len(x)<=1:
            return section_code
        linea = x[0:len(x)-1] if x[len(x)-1]=='\r' else x # para quitar \r
        linea = linea.split(" ")
        widget_name = linea[0]
        instances = linea[1:len(linea)]
        uri_manager = know_data_manager(widget_name)
        # get_item(self,name,widget=True)
        with Pyro4.Proxy(uri_manager) as remote_manager:
            params, code = remote_manager.get_item(widget_name)
            if not(params):
                return None
            dic = create_dictionary(params[0].split(),instances)
            section_code += render_template_string(code,**dic)
    return section_code

def create_dictionary(params, instances):
    my_dict = {}

    for i in range(0,len(params)):
        my_dict[params[i]] = instances[i]

    return my_dict
        
        
# si se trata de una pagina entonces params = (header,nav,section,aside,footer)
# cada section es una lis[string]
def append_item_system(name,params,code,widget=True):
    #widget = (name,hash,estado,params)
    #append_item(self,name,estado,params,code,widget = True)
    manager = know_data_manager(name,widget=widget)
    with Pyro4.Proxy(manager) as manager_remote:
        sol = manager_remote.append_item(name,'propio',params,code,widget = widget)
        return sol
            
'''
El param de las paginas es un string:
    param = section-1 * .... * section-n
    sections = header, nav, section, aside, footer
    section-k = #widget-1 params_to_1 .... #widget-n params_to_n
'''
def know_data_manager(name,widget=True):
    return mi_uri
    hashy = my_hash(name)
    uri = my_chord_widget if widget else my_chord_page
    with Pyro4.Proxy(uri) as chord:
        sucessor = chord.find_sucessor(hashy)
    return sucessor['manager_uri']
    

    
def exists_name_system(name,widget=True):
    #exists_tupla(self,name,widget=True)
    manager = know_data_manager(name,widget=widget)
    with Pyro4.Proxy(manager) as manager_remote:
        sol = manager_remote.exists_tupla(name,widget=widget)
        return sol


def generar_params_page(header,nav,section,aside,footer):
    return generate_section(header) +"*"+generate_section(nav)+"*"+generate_section(section)+"*"+generate_section(aside)+"*"+generate_section(footer)


def generate_section(section):
    sol = ''
    for i in range(0,len(section)-1): 
       sol += "#"+section[i][0:len(section[i])-1]  #para quitar \r 
    sol += "#"+section[len(section)-1]
    return sol

'''
    MANAGER
delete_item(self, name, widget = True)
append_item(self,name,estado,params,code,widget = True)
interval(self,a,b,bajo_exclude = False, alto_exclude = False, widget = True,where="")
delete_interval(self,a,b,bajo_exclude = False, alto_exclude = False, widget = True, estatus="")
get_interval(self,a,b,bajo_exclude = False, alto_exclude = False, widget = True)
change_labels_interval(self,a,b,estado_req, estado_final, bajo_exclude = False, alto_exclude = False, widget=True)
exists_tupla(self,name,widget=True)

    CHORD
find_sucessor(self, key: int)

actualNode: dict = {'chordId': self.chordId, 'address': self.address, 'uri': self.uri,
                            'manager_uri': self.data_manager_uri}
'''