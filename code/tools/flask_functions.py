import sys

import Pyro4
from flask import render_template_string
from tools import ns_workers
from hashlib import sha1


# todo esto me lo puedo ahorrar si creo una clase para la parte de los procesos del chord

def my_chord_uri(widget=True) -> str:
    my_ns = ns_workers.NSFinder().get_own_ns()
    uri = ''

    with Pyro4.Proxy(my_ns) as my_name_server:
        if widget:
            uri = my_name_server.lookup('chord_widgets')

        else:
            uri = my_name_server.lookup('chord_pages')

    return uri

# esto se puede modificar para no estar haciendo broadcast, basta con pedirselo al proceso del chord en sus propiedades
my_chord_widget = ''
my_chord_page = ''


def my_hash(name) -> int:
    return int(sha1(bytes(name, 'utf-8')).hexdigest(), 16)


def armar_pagina(name, header: list, nav: list, section: list, aside: list, footer: list) -> str:
    todo = [header, nav, section, aside, footer]
    for i in range(0, len(todo)):
        todo[i] = crear_section(todo[i])
        if todo[i] == None:  # se puso un widget q no existe
            return None

    dic = {'header': todo[0], 'nav': todo[1], 'section': todo[2], 'aside': todo[3], 'footer': todo[4]}

    dic["page_name"] = name

    script = r"window.onload = function(){ 'use strict'; var milliseconds = 5000; window.setTimeout(function(){ " \
             r"document.location.reload(); }, milliseconds); };"

    with open("{path}/templates/base_pages.html".format_map({'path': sys.path[0]})) as file:
        code = file.read()

    dic['code'] = script

    with open("{path}/static/estilo.css".format_map({'path': sys.path[0]})) as file_css:
        css = file_css.read()

    dic["estilo"] = css

    return code.format_map(dic)


def crear_section(list_widget: list) -> str:
    section_code = ""
    for x in list_widget:
        if len(x) <= 1:
            return section_code
        linea = x[0: len(x) - 1] if x[len(x) - 1] == '\r' else x  # para quitar \r,
        linea = linea.split(" ")
        widget_name = linea[0]
        instances = linea[1: len(linea)]
        uri_manager = know_data_manager(widget_name)
        # get_item(self,name,widget=True)
        with Pyro4.Proxy(uri_manager) as remote_manager:
            params, code = remote_manager.get_item(widget_name)
            if not params and not code:  # el item no existe
                return None
            dic = create_dictionary(params.split(), instances) if params else {}
            section_code += render_template_string(code, **dic)

    return section_code


def create_dictionary(params: list, instances: list) -> dict:
    my_dict = {}

    for i in range(0, len(params)):
        print('los parametros del widget son: ' + str(params))
        print(i)
        my_dict[params[i]] = instances[i]

    return my_dict


# si se trata de una pagina entonces params = (header,nav,section,aside,footer)
# cada section es una lis[string]
def append_item_system(name, params, code, widget=True):
    # widget = (name,hash,estado,params)
    manager = know_data_manager(name, widget=widget)

    try:
        with Pyro4.Proxy(manager) as manager_remote:
            manager_remote._pyroTimeout = 7
            manager_remote.append_item(name, code, widget=widget, params=params, estado='propio')

    except (Pyro4.errors.TimeoutError, Pyro4.errors.CommunicationError,): return False

    return True



# '''
# El param de las paginas es un string:
#     param = section-1 * .... * section-n
#     sections = header, nav, section, aside, footer
#     section-k = #widget-1 params_to_1 .... #widget-n params_to_n
# '''


def know_data_manager(name, widget=True):
    hashy = my_hash(name)
    uri = my_chord_widget if widget else my_chord_page

    with Pyro4.Proxy(uri) as chord:
        sucessor = chord.find_sucessor(hashy)

    print(sucessor)

    return sucessor['manager_uri']


def exists_name_system(name, widget=True):
    # exists_tupla(self,name,widget=True)
    manager = know_data_manager(name, widget=widget)

    with Pyro4.Proxy(manager) as manager_remote:
        sol = manager_remote.exists_tupla(name, widget=widget)

    return sol


def generar_params_page(header: list, nav: list, section: list, aside: list, footer: list) -> str:
    return generate_section(header) + "*" + generate_section(nav) + "*" + generate_section(
        section) + "*" + generate_section(aside) + "*" + generate_section(footer)


def generate_section(section: list) -> str:
    sol = ''
    for i in range(0, len(section) - 1):
        sol += "#" + section[i][0:len(section[i]) - 1]  # para quitar \r Ray: todo esto puede no servir, hay otra forma
    sol += "#" + section[len(section) - 1]
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
