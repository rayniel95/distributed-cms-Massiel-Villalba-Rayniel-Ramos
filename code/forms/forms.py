from flask_wtf import Form
from wtforms import StringField, SubmitField, TextAreaField, FieldList
from wtforms.validators import Required, Length



class Crear_pagina(Form):
    nombre_pagina = StringField("Nombre de la pagina", validators=[Required(),Length(3,20)])
    header = TextAreaField("Header")
    nav = TextAreaField("Nav")
    section = TextAreaField("Section")
    aside = TextAreaField("Aside")
    footer = TextAreaField("Footer")
    submit = SubmitField('Crear')

'''
El param de las paginas es un string:
    param = section-1 * .... * section-n
    sections = header, nav, section, aside, footer
    section-k = #widget-1 params_to_1 .... #widget-n params_to_n
'''

class Crear_widget(Form):
    name = StringField("Nombre del widget", validators=[Required(),Length(3,20)])
    params = StringField("Parametros")
    codigo = TextAreaField("Inserte codigo", validators=[Required()])
    submit = SubmitField('Crear')