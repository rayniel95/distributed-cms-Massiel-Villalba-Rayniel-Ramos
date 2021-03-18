'''
main script for general routines
'''
import time

import Pyro4
from Pyro4 import socketutil
from flask import Flask, render_template, redirect, render_template_string
from flask_bootstrap import Bootstrap

from chord_process import ChordProcess
from forms.forms import Crear_pagina, Crear_widget
from tools import flask_functions
from tools import listers

# todo ver lo del nombre en un futuro
sdApp = Flask(__name__)
sdApp.config['SECRET_KEY'] = 'hard to guess string'
bootstrap = Bootstrap(sdApp)

chord_process = ChordProcess(host=socketutil.getIpAddress('localhost', workaround127=True))

mi_manager_uri = chord_process.uri_dm


with Pyro4.Proxy(mi_manager_uri) as mi_manager:
    mi_manager._pyroTimeout = 7
    mi_manager.limpiar(widget=False)
    mi_manager.limpiar()

chord_process.go()

chord_widgets_uri = chord_process.chord_widgets.uri
chord_pages_uri = chord_process.chord_pages.uri

flask_functions.my_chord_widget = chord_widgets_uri
flask_functions.my_chord_page = chord_pages_uri

# todo ver lo de los trys, parece q van por fuera
# todo ver lo de la reconeccion y lo del timeout
# todo poner los print del chord para q digan tambien a q chord pertenecen

# todo falta borrarle la info a mi sucesor
# todo falta en el caso de q yo sea el unico nodo en la red y tenga muertos en la finger ponerme a mi como sucesor de
# la llave

@sdApp.route('/')
def index():
    return render_template('index.html')


@sdApp.route('/widget_creator/', methods=['GET', 'POST'])
def viewWidgetCreator():
    form = Crear_widget()
    if form.validate_on_submit():
        name = form.name.data
        params = form.params.data
        code = form.codigo.data

        if (flask_functions.exists_name_system(name)):
            message2 = "<h6>Ya existe un widget con ese nombre en el sistema</h6><br>"
            return message2 + render_template('widgetCreator.html', form=form)

        flask_functions.append_item_system(name, params, code)

        return redirect('/')

    return render_template('widgetCreator.html', form=form)


@sdApp.route('/page_list/')
def viewPageList():
    pages = listers.Lister().list_all(False)

    return render_template('pageList.html', page_list=pages)


@sdApp.route('/page_creator', methods=['POST', 'GET'])
def viewPageCreator():
    form = Crear_pagina()
    if form.validate_on_submit():
        name = form.nombre_pagina.data
        header = form.header.data.split("\n")
        nav = form.nav.data.split("\n")
        section = form.section.data.split("\n")
        aside = form.aside.data.split("\n")
        footer = form.footer.data.split("\n")

        params = flask_functions.generar_params_page(header, nav, section, aside, footer)
        code = flask_functions.armar_pagina(name, header, nav, section, aside, footer)
        if not code:
            return "<h6>Alguno de los widgets referidos para disenar la pagina no existe en el sistema</h6>"

        flask_functions.append_item_system(name, params, code, widget=False)

        return redirect('/')

    return render_template('pageCreator.html', form=form)

@sdApp.route('/page_list/<page_name>')
def viewPage(page_name: str):
    # si ya la pagina esta cacheada no la busco

    page = [None, None]
    with Pyro4.Proxy(mi_manager_uri) as my_manager:
        if my_manager.exists_tupla(page_name, widget=False):  # puede pasar q sea un propio falso y q no se actualice

                page[1] = my_manager.leer_archivo(page_name, widget=False)

    if page[1]: return render_template_string(page[1])
    # si el tipo esta muerto me van a dar un dict vacio pq la finger aun no se actualiza
    manager_uri = flask_functions.know_data_manager(page_name, widget=False)

    for _ in range(3):

        with Pyro4.Proxy(manager_uri) as remote_manager:
            remote_manager._pyroTimeout = 3
            page = remote_manager.get_item(page_name, widget=False)

        if page[0]: break

        time.sleep(3)

    if not page[0]: return 'Nothing'

    with Pyro4.Proxy(mi_manager_uri) as my_dm:
        my_dm.append_item(page_name, page[1], widget=False, params=page[0], estado='cache')

    return page[1]


@sdApp.route('/widget_list/')
def viewWidgetList():
    widgets = listers.Lister().list_all(True)

    return render_template('widgetList.html', widget_list=widgets)

# solo se ejecutara cuando se llame al script y no cuando se llame a su funcion main