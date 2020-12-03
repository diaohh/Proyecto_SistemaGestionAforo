#Framework usado: Flask
from flask import Flask, render_template, redirect, url_for, request, jsonify, flash, session
from flask_bcrypt import Bcrypt

#Analisis de imagenes con codigos QR
from pyzbar.pyzbar import decode
from PIL import Image

#Generacion de imagen QR
import pyqrcode

#Manejo de tiempos
from datetime import date,timedelta,datetime
from time import time

#Libreria para conexion con la base de datos
from pymongo import MongoClient

#Usado para insertar el valor NaN en la base de datos
from numpy import nan

#Libreria para el uso del correo electronico
from email.message import EmailMessage
import smtplib

#Pasar base de datos como parametro
from sys import argv

#Mensajes predefinidos de respuesta automatica
from mensajes import *

#aplicativo flask
app = Flask(__name__)
#Modulo para encriptacion de contraseñas
bcrypt = Bcrypt(app)
#Coneccion con la base de datos recibida como parametro en el llamado
cliente = MongoClient(argv[1])
bd = cliente['projectdb']

usuario_correo = argv[2]
contrasena_correo = argv[3]


def enviar_correo(destino, asunto, mensaje, imagen):
	msj = EmailMessage()
	msj['Subject'] = asunto
	msj['From'] = usuario_correo
	msj['To'] = destino
	msj.set_content(mensaje)

	if len(imagen):
		with open(imagen,'rb') as img:
			archivo = img.read()
			nombre = img.name
		msj.add_attachment(archivo,maintype='image',subtype='png',filename="Codigo_QR.png")

	with smtplib.SMTP_SSL('smtp.gmail.com',465) as smtp:
		smtp.login(usuario_correo,contrasena_correo)
		smtp.send_message(msj)


@app.route("/")
def index():
	"""
	Pagina principal, si no se ha iniciado una sesion, se
	muestra el menu principal de la pagina, de lo contrario
	se muestran los distintos menus dependiendo del tipo de
	cuenta en sesion

	"""
	if "tipo" in session:
		
		if session["tipo"] == 1:
			visitas_aux = bd['visita']
			visitas_aux = visitas_aux.find({"ingreso":"SI","tipo_id_persona":session['tipo_id'], "num_id_persona":session['num_id']})
			visitas = list()
			for visita in visitas_aux:
				comercio = bd['comercio'].find({"tipo_id":visita['tipo_id_local'], "num_id":visita['num_id_local']})
				visitas.append((comercio[0]['nombre'],visita['fechayhora']))

			return render_template("usuario.html", visitas=visitas)
		
		if session["tipo"] == 2:
			visitas = list()
			for v in bd['visita'].find({'tipo_id_local':session['tipo_id'], 'num_id_local':session['num_id']}):
				visitas.append((v['tipo_id_persona'],v['num_id_persona'],v['fechayhora'],v['tapabocas'],v['temperatura'],v['ingreso']))

			return render_template("local.html",visitas=visitas)

		if session["tipo"] == 3:
			pruebas = list()
			for p in bd['historial_pruebas'].find({'tipo_id_entidad':session['tipo_id'], 'num_id_entidad':session['num_id']}):
				pruebas.append((p['id_historial'],p['tipo_id_persona'],p['num_id_persona'],p['fechayhora'],p['resultado']))

			return render_template("entidad_sanitaria.html",pruebas=pruebas)
		if session["tipo"] == 4:
			return render_template("admin.html")
	else:
		return render_template("index.html")


@app.route("/objetivo")
def objetivo():
	"""
	Retorna pagina de objetivos
	"""
	return render_template("objetivo.html")


@app.route("/contactanos")
def contactanos():
	"""
	Retorna pagina con informacion de contacto
	"""
	return render_template("contactanos.html")


@app.route("/inicio-sesion/",methods=["GET","POST"])
def inicio_sesion():
	"""
	Retorna menu de inicio de sesion, y redirecciona
	al momento de enviar el formulario diligenciado
	"""
	
	if request.method =='GET':
		if 'tipo' not in session:
			return render_template("inicio_de_sesion.html")
		else:
			return redirect(url_for("index"))
	else: 
		usuario = request.form['usuario']
		contrasena = request.form['contrasena']
		tipo_cuenta = 0 # 1: Civil, 2: Comercio, 3: Entidad Sanitaria, 4: admin

		usuario_bd = bd['civil'].find_one({'usuario':usuario})
		if usuario_bd:
			if bcrypt.check_password_hash(usuario_bd['contrasena'].encode('utf-8'),contrasena.encode('utf-8')):
				if usuario_bd['pendiente'] == 1:
					flash('pendiente')
					return render_template("inicio_de_sesion.html")
				else:
					session['usuario'] = usuario
					session['tipo'] = 1
					session['tipo_id'] = usuario_bd['tipo_id']
					session['num_id'] = usuario_bd['num_id']
		
		usuario_bd = bd['comercio'].find_one({'usuario':usuario})
		if usuario_bd:
			if bcrypt.check_password_hash(usuario_bd['contrasena'].encode('utf-8'),contrasena.encode('utf-8')):
				if usuario_bd['pendiente'] == 1:
					flash('pendiente')
					return render_template("inicio_de_sesion.html")
				else:
					session['usuario'] = usuario
					session['tipo'] = 2
					session['tipo_id'] = usuario_bd['tipo_id']
					session['num_id'] = usuario_bd['num_id']
		
		usuario_bd = bd['entidad_sanitaria'].find_one({'usuario':usuario})
		if usuario_bd:
			if bcrypt.check_password_hash(usuario_bd['contrasena'].encode('utf-8'),contrasena.encode('utf-8')):
				if usuario_bd['pendiente'] == 1:
					flash('pendiente')
					return render_template("inicio_de_sesion.html")
				else:
					session['usuario'] = usuario
					session['tipo'] = 3
					session['tipo_id'] = usuario_bd['tipo_id']
					session['num_id'] = usuario_bd['num_id']
		
		usuario_bd = bd['administrador'].find_one({'usuario':usuario})
		if usuario_bd:
			if usuario_bd['contrasena'] == contrasena:
				session['usuario'] = usuario
				session['tipo'] = 4

		if len(session): return redirect(url_for("index"))
		flash('incorrecto')
		return render_template("inicio_de_sesion.html")


@app.route("/mi-cuenta/",methods=["GET","POST"])
def mi_cuenta():
	"""
	Retorna formulario para solicitudes de cambios
	de datos, siempre y cuando no se haya realizado
	otra solicitud previamente
	"""
	if 'tipo' not in session:
		return redirect(url_for("index"))
	
	elif session['tipo'] == 1:
		usuario = list(bd['civil'].find_one({
			'tipo_id':session['tipo_id'],
			'num_id':session['num_id']
		}).values())

		barrio = list(bd['barrio'].find_one({
			'id_barrio':usuario[9]
		}).values())

		departamentos = list()
		dep = bd['departamento'].find({})
		for u in dep:
			departamentos.append(u['nombre'])

		return render_template('usuario_cuenta.html',usuario=usuario,barrio=barrio,departamentos=departamentos)

	
	elif session['tipo'] == 2: 
		pass
	
	elif session['tipo'] == 3: 
		pass
	
	elif session['tipo'] == 4:
		pass


@app.route("/cerrar-sesion/")
def cerrar_sesion():
	"""
	Cierra la sesion en cuestion y redirecciona al menu
	principal
	"""
	session.clear()
	return redirect(url_for("index"))

@app.route("/registro-usuario/",methods=["GET","POST"])
def registro_usuario():
	"""
	Retorna formulario para registro de usuarios e
	inscribe los usuarios en la base de datos como
	pendientes de aceptacion.
	"""
	
	if request.method == 'GET':
		departamentos = list()
		dep = bd['departamento'].find({})
		for u in dep:
			departamentos.append(u['nombre'])

		return render_template("usuario_registro.html", departamentos=departamentos)
	else:
		tipo_id = request.form['tipo_id']
		num_id = request.form['num_id']
		nombres = request.form['nombre']	
		apellidos = request.form['apellido']
		genero = request.form['genero']
		nacimiento = request.form['nacimiento']

		municipio = request.form['municipio']
		barrio = request.form['barrio']
		
		id_barrio = bd['barrio'].find({'nombre':barrio,'municipio':municipio})[0]['id_barrio']

		direccion = request.form['direccion']
		correo = request.form['correo']
		telefono = request.form['telefono']
		usuario = request.form['usuario']
		contrasena = (bcrypt.generate_password_hash(request.form['contrasena'].encode('utf-8'))).decode('utf-8')
		
		bd['civil'].insert_one({
			'tipo_id':tipo_id,
			'num_id': num_id,
			'usuario': usuario,
			'contrasena':contrasena,
			'nombres':nombres,
			'apellidos':apellidos,
			'genero':genero,
			'nacimiento':nacimiento,
			'id_barrio':id_barrio,
			'direccion':direccion,
			'correo':correo,
			'telefono':telefono,
			'pendiente':1
		})
		flash('registro')
		return redirect(url_for("index"))


@app.route("/registro-local/",methods=["GET","POST"])
def registro_local():
	"""
	Retorna formulario para registro de locales e
	inscribe los locales en la base de datos como
	pendientes de aceptacion.
	"""

	if request.method == 'GET':
		departamentos = list()
		dep = bd['departamento'].find({})
		for u in dep:
			departamentos.append(u['nombre'])

		categorias = list()
		cat = bd['categoria'].find({})
		for u in cat:
			categorias.append(u['nombre'])

		return render_template("local_registro.html", departamentos=departamentos,categorias=categorias)
	else:
		tipo_id = request.form['tipo_id']
		num_id = request.form['num_id']
		nombre = request.form['nombre']
		
		municipio = request.form['municipio']
		barrio = request.form['barrio']

		id_barrio = bd['barrio'].find({'nombre':barrio,'municipio':municipio})[0]['id_barrio']

		correo = request.form['correo']
		categoria = request.form['categoria']
		telefonos = int(request.form['telefonos'])
		telefono1 = request.form['telefono1']
		telefono2, telefono3 = nan,nan
		if telefonos > 1: telefono2 = request.form['telefono2']
		if telefonos > 2: telefono3 = request.form['telefono3']
		usuario = request.form['usuario']
		contrasena = (bcrypt.generate_password_hash(request.form['contrasena'].encode('utf-8'))).decode('utf-8')
		
		bd['comercio'].insert_one({
			'tipo_id':tipo_id,
			'num_id': num_id,
			'usuario': usuario,
			'contrasena':contrasena,
			'nombre':nombre,
			'id_barrio':id_barrio,
			'correo':correo,
			'categoria':categoria,
			'telefono1':telefono1,
			'telefono2':telefono2,
			'telefono3':telefono3,
			'pendiente':1
		})

		flash('registro')
		return redirect(url_for("index"))


@app.route("/registro-entidad-salud/",methods=["GET","POST"])
def registro_entidad_salud():
	"""
	Retorna formulario para registro de entidades de
	salud inscribe los entidades de salud en la base
	de datos como pendientes de aceptacion.
	"""

	if request.method == 'GET':
		departamentos = list()
		dep = bd['departamento'].find({})
		for u in dep:
			departamentos.append(u['nombre'])

		return render_template("entidad_sanitaria_registro.html", departamentos=departamentos)
	else:
		tipo_id = request.form['tipo_id']
		num_id = request.form['num_id']
		nombre = request.form['nombre']
		
		municipio = request.form['municipio']
		barrio = request.form['barrio']

		id_barrio = bd['barrio'].find({'nombre':barrio,'municipio':municipio})[0]['id_barrio']

		correo = request.form['correo']
		telefono = request.form['telefono']
		
		usuario = request.form['usuario']
		contrasena = (bcrypt.generate_password_hash(request.form['contrasena'].encode('utf-8'))).decode('utf-8')
		
		bd['entidad_sanitaria'].insert_one({
			'tipo_id':tipo_id,
			'num_id': num_id,
			'usuario': usuario,
			'contrasena':contrasena,
			'nombre':nombre,
			'id_barrio':id_barrio,
			'correo':correo,
			'telefono':telefono,
			'pendiente':1
		})

		flash('registro')
		return redirect(url_for("index"))

	return render_template("entidad_sanitaria_registro.html")


@app.route("/muns/<dep>")
def obtener_municipios(dep):
	"""
	Recibe el nombre de un departamento y retorna
	una pagina en formato Json con los municipios
	correspondientes.
	"""
	municipios = list()
	for m in bd['municipio'].find({'departamento':dep}): municipios.append(m['nombre'])
	return jsonify({'municipios':municipios})


@app.route("/barrios/<mun>")
def obtener_barrios(mun):
	"""
	Recibe el nombre de un municipio y retorna
	una pagina en formato Json con los barrios
	correspondientes.
	"""
	barrios = list()
	for b in bd['barrio'].find({'municipio':mun}): barrios.append(b['nombre'])
	return jsonify({'barrios':barrios})


@app.route("/id/<tipo_tabla>/<tipo_id>/<num_id>")
def obtener_documentos(tipo_tabla,tipo_id,num_id):
	"""
	Recibe: tipo_tabla siendo el nombre de la tabla
	a la cual se quiere acceder (civil, comercio,
	admin, entidad_sanitaria), tipo_id (CC, TI, TE,
	NIT, RUT), num_id con los que retorna una pagina
	en formato Json, se usa para verificar la
	existencia de un documento en la base de datos.
	"""
	docs = list()
	for u in bd[tipo_tabla].find({'tipo_id':tipo_id,'num_id':num_id}): docs.append(u['tipo_id'])
	return jsonify({'docs':docs})


@app.route("/user/<usr>")
def obtener_usuarios(usr):
	"""
	Recibe un nombre de usuario, con el cual verifica
	su existencia en la base de datos y retorna una
	pagina en formato Json en la cual si esta vacia,
	indica que el usuario no existe en la base de datos
	en general.
	"""
	usuarios = list()
	for u in bd['civil'].find({'usuario':usr}): usuarios.append(u['usuario']) 
	for u in bd['administrador'].find({'usuario':usr}): usuarios.append(u['usuario']) 
	for u in bd['comercio'].find({'usuario':usr}): usuarios.append(u['usuario']) 
	for u in bd['entidad_sanitariad'].find({'usuario':usr}): usuarios.append(u['usuario']) 
	
	return jsonify({'usuarios':usuarios})


@app.route("/local-QR/",methods=["GET","POST"])
def local_QR():
	"""
	Retorna la pagina para inscripcion por codigo QR
	para el usuario local.
	"""
	if "tipo" not in session or session['tipo'] != 2:
		return redirect(url_for("index"))
	if request.method == "GET":
		return render_template("local_QR.html")
	else:
		#Decodificar imagen QR
		aux1 = decode(Image.open(request.files['codigo_QR']))
		#Leer informacion del codigo QR
		aux = aux1[0].data.decode('ascii')
		tipo_id, num_id = aux[:2],aux[3:]
		
		usuario = bd['civil'].find({'tipo_id':tipo_id,'num_id':num_id})
		if not usuario.count():
			flash('no_usuario')
			return render_template("local_QR.html")
		
		prueba = list()
		for p in bd['historial_pruebas'].find({'tipo_id_persona':tipo_id,'num_id_persona':num_id}):  
			prueba.append((datetime.strptime(p['fechayhora'], '%Y-%m-%d %H:%M:%S'),p['resultado']))

		permitido = 1
		if len(prueba):
			prueba = min(prueba, key=lambda x: x[0])
			#Si no se ha hecho una prueba de COVID-19 en los ultimos 15 dias, debe estar en cuarentena
			fecha = prueba[0]
			fechaMin = date.today() - timedelta(days=15)
			if prueba[1]!='Negativo' and fecha >= fechaMin: permitido = 0

		tapabocas = 'SI'
		if 'tapabocas' not in request.form:
			permitido = 0
			tapabocas = 'NO'

		if not 35<=float(request.form['temp'])<38: permitido = 0

		if permitido: ingreso = 'SI'
		else: ingreso = 'NO'

		fechayhora = datetime.fromtimestamp(time()).strftime('%Y-%m-%d %H:%M:%S')
		bd['visita'].insert_one({
			'tipo_id_persona':tipo_id,
			'num_id_persona': num_id,
			'fechayhora': fechayhora,
			'tipo_id_local':session['tipo_id'],
			'num_id_local':session['num_id'],
			'tapabocas':tapabocas,
			'temperatura':request.form['temp'],
			'ingreso':ingreso
		})

		if not permitido: flash('no_apto')
		return redirect(url_for("index"))


@app.route("/local-no-QR/",methods=["GET","POST"])
def local_no_QR():
	"""
	Retorna la pagina para inscripcion sin codigo QR
	para el usuario local.
	"""
	if "tipo" not in session or session['tipo'] != 2:
		return redirect(url_for("index"))
	if request.method == "GET":
		return render_template("local_no_QR.html")
	else:
		tipo_id, num_id = request.form['tipo_id'], request.form['num_id']
		
		usuario = bd['civil'].find({'tipo_id':tipo_id,'num_id':num_id})
		if not usuario.count():
			flash('no_usuario')
			return render_template("local_no_QR.html")

		prueba = list()
		for p in bd['historial_pruebas'].find({'tipo_id_persona':tipo_id,'num_id_persona':num_id}):  
			prueba.append((datetime.strptime(p['fechayhora'], '%Y-%m-%d %H:%M:%S'),p['resultado']))

		permitido = 1
		if len(prueba):
			prueba = max(prueba, key=lambda x: x[0])
			#Si no se ha hecho una prueba de COVID-19 en los ultimos 15 dias, debe estar en cuarentena
			fecha = prueba[0]
			fechaMin = datetime.today() - timedelta(days=15)
			if prueba[1]!='Negativo' and fecha >= fechaMin: permitido = 0

		tapabocas = 'SI'
		if 'tapabocas' not in request.form:
			permitido = 0
			tapabocas = 'NO'

		if not 35<=float(request.form['temp'])<38: permitido = 0

		if permitido: ingreso = 'SI'
		else: ingreso = 'NO'

		fechayhora = datetime.fromtimestamp(time()).strftime('%Y-%m-%d %H:%M:%S')
		bd['visita'].insert_one({
			'tipo_id_persona':tipo_id,
			'num_id_persona': num_id,
			'fechayhora': fechayhora,
			'tipo_id_local':session['tipo_id'],
			'num_id_local':session['num_id'],
			'tapabocas':tapabocas,
			'temperatura':request.form['temp'],
			'ingreso':ingreso
		})

		if not permitido: flash('no_apto')
		return redirect(url_for("index"))


@app.route("/local-destiempo/",methods=["GET","POST"])
def local_destiempo():
	"""
	Retorna la pagina para inscripcion a destiempo
	para el usuario local.
	"""
	if "tipo" not in session or session['tipo'] != 2:
		return redirect(url_for("index"))
	if request.method == "GET":
		return render_template("local_no_QR_des.html")
	else:
		tipo_id, num_id = request.form['tipo_id'], request.form['num_id']
		
		usuario = bd['civil'].find({'tipo_id':tipo_id,'num_id':num_id})
		if not usuario.count():
			flash('no_usuario')
			return render_template("local_no_QR_des.html")

		permitido = 1
		tapabocas = 'SI'
		if 'tapabocas' not in request.form:
			permitido = 0
			tapabocas = 'NO'

		if not 35<=float(request.form['temp'])<38: permitido = 0

		if permitido: ingreso = 'SI'
		else: ingreso = 'NO'

		fechayhora = datetime.strptime(request.form['fecha']+' '+request.form['hora']+':00', '%Y-%m-%d %H:%M:%S')
		bd['visita'].insert_one({
			'tipo_id_persona':tipo_id,
			'num_id_persona': num_id,
			'fechayhora': fechayhora,
			'tipo_id_local':session['tipo_id'],
			'num_id_local':session['num_id'],
			'tapabocas':tapabocas,
			'temperatura':request.form['temp'],
			'ingreso':ingreso
		})

		return redirect(url_for("index"))


@app.route("/registro-prueba/",methods=["POST"])
def registro_prueba():
	"""
	Realiza el registro de una prueba realizada a la base de datos
	"""
	if 'tipo' in session and session['tipo'] == 3:
		
		tipo_id, num_id = request.form['tipo_id1'], request.form['num_id1']
		usuario = bd['civil'].find({'tipo_id':tipo_id,'num_id':num_id})
		if not usuario.count():
			flash('no_usuario')
			return redirect(url_for("index"))

		N = bd['historial_pruebas'].find({'id_historial':request.form['prueba_id1'],'tipo_id_entidad':session['tipo_id'],'num_id_entidad':session['num_id']}).count()
		if N:
			flash('no_historial')
			return redirect(url_for("index"))

		prueba = bd['historial_pruebas'].find({'tipo_id_persona':tipo_id,'num_id_persona':num_id,'tipo_id_entidad':session['tipo_id'],'num_id_entidad':session['num_id'],'resultado':'Ninguno'})
		if prueba.count():
			flash('pendiente')
			return redirect(url_for("index"))

		fechayhora = datetime.fromtimestamp(time()).strftime('%Y-%m-%d %H:%M:%S')
		bd['historial_pruebas'].insert_one({
			'id_historial':request.form['prueba_id1'],
			'tipo_id_persona': request.form['tipo_id1'],
			'num_id_persona': request.form['num_id1'],
			'tipo_id_entidad':session['tipo_id'],
			'num_id_entidad':session['num_id'],
			'fechayhora':fechayhora,
			'resultado':'Ninguno'
		})


		return redirect(url_for("index"))


@app.route("/registro-resultado/",methods=["POST"])
def registro_resultado():
	"""
	Realiza el registro del resultado de una prueba previamente
	realizada en la base de datos
	"""
	if 'tipo' in session and session['tipo'] == 3:
		N = bd['historial_pruebas'].find({'id_historial':request.form['prueba_id2'],'tipo_id_entidad':session['tipo_id'],'num_id_entidad':session['num_id']})
		if not N.count():
			flash('no_prueba')
			return redirect(url_for("index"))

		N = N[0]
		if N['resultado'] != "Ninguno":
			flash('reportado')
			return redirect(url_for("index"))

		bd['historial_pruebas'].update_one({'id_historial':request.form['prueba_id2'],'tipo_id_entidad':session['tipo_id'],'num_id_entidad':session['num_id']},{'$set':{'resultado':request.form['desicion']}})
		
		return redirect(url_for("index"))


@app.route("/gestionar-locales/")
def gestionar_locales():
	"""
	Retorna la pagina de gestion de locales para el usuario
	administrador
	"""
	if 'tipo' not in session or session['tipo'] != 4:
		return redirect(url_for("index"))

	locales = list()
	for l in bd['comercio'].find({'pendiente':0}):
		aux = list(l.values())
		if str(aux[10]) == 'nan': aux[10] = 'N/A'
		if str(aux[11]) == 'nan': aux[11] = 'N/A'
		barrio = bd['barrio'].find_one({'id_barrio':aux[6]})
		aux.append(barrio['municipio'])
		aux.append(barrio['nombre'])
		locales.append(aux)

	return render_template("admin_gestionarLocales.html",locales=locales)


@app.route("/gestionar-entidades-sanitarias/")
def gestionar_entidades_sanitarias():
	"""
	Retorna la pagina de gestion de entidades de salud
	para el usuario administrador
	"""
	if 'tipo' not in session or session['tipo'] != 4:
		return redirect(url_for("index"))

	entidades = list()
	for es in bd['entidad_sanitaria'].find({'pendiente':0}):
		aux = list(es.values())
		barrio = bd['barrio'].find_one({'id_barrio':int(aux[6])})
		aux.append(barrio['municipio'])
		aux.append(barrio['nombre'])
		entidades.append(aux)

	return render_template("admin_gestionarEntidadesSanitarias.html",entidades=entidades)


@app.route("/gestionar-solicitudes/")
def gestionar_solicitudes():
	"""
	Retorna el menu para gestion de solicitudes para el 
	usuario administrador
	"""
	if 'tipo' not in session or session['tipo'] != 4:
		return redirect(url_for("index"))

	return render_template("admin_gestionarSolicitudes.html")


@app.route("/gestionar-usuarios/")
def gestionar_usuarios():
	"""
	Retorna la pagina de gestion de civiles
	para el usuario administrador
	"""
	if 'tipo' not in session or session['tipo'] != 4:
		return redirect(url_for("index"))

	usuarios = list()
	for l in bd['civil'].find({'pendiente':0}):
		aux = list(l.values())
		barrio = bd['barrio'].find_one({'id_barrio':aux[9]})
		aux.append(barrio['municipio'])
		aux.append(barrio['nombre'])
		usuarios.append(aux)

	return render_template("admin_gestionarUsuarios.html",usuarios=usuarios)


@app.route("/gestionar-admins/",methods=['GET','POST'])
def gestionar_admins():
	"""
	Retorna la pagina de gestion de administradores
	para el usuario administrador
	"""
	if 'tipo' not in session or session['tipo'] != 4:
		return redirect(url_for("index"))
	
	if request.method == 'POST':
		nombre = request.form['nombre']
		apellido = request.form['apellido']
		usuario = request.form['usuario']
		contrasena = request.form['contrasena']

		N = 0
		usuarios = list()
		N += bd['civil'].find({'usuario':usuario}).count()
		N += bd['administrador'].find({'usuario':usuario}).count()
		N += bd['comercio'].find({'usuario':usuario}).count()
		N += bd['entidad_sanitariad'].find({'usuario':usuario}).count()

		if N:
			flash('no_usuario')
		else:	
			bd['administrador'].insert_one({
				'usuario':usuario,
				'contrasena': contrasena,
				'nombres': nombre,
				'apellidos':apellido
			})

	administradores = list()
	for l in bd['administrador'].find({}): administradores.append(list(l.values()))

	return render_template("admin_gestionarAdmins.html",administradores=administradores)


@app.route("/gestionar-barrios/",methods=['GET','POST'])
def gestionar_barrios():
	"""
	Retorna la pagina para gestion de barrios para el
	usuario administrador
	"""
	if 'tipo' not in session or session['tipo'] != 4:
		return redirect(url_for("index"))

	if request.method =='POST':
		if 'id_barrio1' in request.form:
			if not bd['barrio'].find_one({'id_barrio':request.form['id_barrio1']}):
				bd['barrio'].insert_one({
				'id_barrio':request.form['id_barrio1'],
				'nombre': request.form['nombre'],
				'municipio': request.form['municipio'],
				'departamento':request.form['departamento']
				})
			else:
				flash('no_id')
		else:
			if bd['barrio'].find_one({'id_barrio':request.form['id_barrio2']}):
				bd['barrio'].delete_one({'id_barrio':request.form['id_barrio2']})
			else:
				flash('no_id_elim')

	departamentos = list()
	for d in bd['departamento'].find({}): departamentos.append(d['nombre'])

	barrios = list()
	for b in bd['barrio'].find({}): barrios.append(list(b.values()))
	
	return render_template("admin_gestionarBarrios.html",barrios=barrios, departamentos=departamentos)


@app.route("/gestionar-categorias/",methods=['GET','POST'])
def gestionar_categorias():
	"""
	Retorna la pagina para gestion de categorias para el
	usuario administrador
	"""
	if 'tipo' not in session or session['tipo'] != 4:
		return redirect(url_for("index"))

	if request.method == 'POST':
		if 'nombre' in request.form:
			if not bd['categoria'].find_one({'nombre':request.form['nombre']}):
				bd['categoria'].insert_one({'nombre':request.form['nombre']})
			else:
				flash('no_nombre')
		else:
			if bd['categoria'].find_one({'nombre':request.form['categoria']}):
				bd['categoria'].delete_one({'nombre':request.form['categoria']})
			else:
				flash('no_nombre_elim')

	categorias = list()
	for c in bd['categoria'].find({}): categorias.append(c['nombre'])

	return render_template("admin_gestionarCategorias.html",categorias=categorias)


@app.route("/gestionar-solicitudes/registro/civil",methods=['GET','POST'])
def gestionar_solicitudes_registro_civil():
	"""
	Retorna la pagina para gestion de solicitudes de
	registro a civiles para el usuario administrador
	"""
	if 'tipo' not in session or session['tipo'] != 4:
		return redirect(url_for("index"))

	if request.method == 'POST':
		tipo_id = request.form['tipo_id']
		num_id = request.form['num_id']
		correo = request.form['correo']
		nombre = request.form['nombre']
		
		if 'aceptar' in request.form:

			QR = pyqrcode.create(tipo_id+'-'+num_id)
			QR.png('QRs/'+tipo_id+'-'+num_id+'.png',scale=8)

			enviar_correo(correo,
				"Solicitud de creacion de cuenta",
				mensaje_aprobacion_civil.format(nombre),
				'QRs/'+tipo_id+'-'+num_id+'.png'
			)

			bd['civil'].update_one({
				'tipo_id':tipo_id,
				'num_id':num_id
			},{
				'$set':{
					'pendiente':0
				}
			})

		else:
			enviar_correo(correo,
				"Solicitud de creacion de cuenta",
				mensaje_rechazo_civil.format(nombre),
				''
			)

			bd['civil'].delete_one({'tipo_id':tipo_id,'num_id':num_id})

	usuarios = list()
	for l in bd['civil'].find({'pendiente':1}):
		aux = list(l.values())
		barrio = bd['barrio'].find_one({'id_barrio':aux[9]})
		aux.append(barrio['municipio'])
		aux.append(barrio['nombre'])
		usuarios.append(aux)

	return render_template("admin_gestionarSolicitudes_registro_usuarios.html",usuarios=usuarios)


@app.route("/gestionar-solicitudes/registro/comercio",methods=['GET','POST'])
def gestionar_solicitudes_registro_comercio():
	"""
	Retorna la pagina para gestion de solicitudes de
	registro a comercios para el usuario administrador
	"""
	if 'tipo' not in session or session['tipo'] != 4:
		return redirect(url_for("index"))

	if request.method == 'POST':
		tipo_id = request.form['tipo_id']
		num_id = request.form['num_id']
		correo = request.form['correo']
		nombre = request.form['nombre']
		
		if 'aceptar' in request.form:

			enviar_correo(correo,
				"Solicitud de creacion de cuenta",
				mensaje_aprobacion_comercio.format(nombre),
				''
			)
			bd['comercio'].update_one({
				'tipo_id':tipo_id,
				'num_id':num_id
			},{
				'$set':{
					'pendiente':0
				}
			})

		else:
			enviar_correo(correo,
				"Solicitud de creacion de cuenta",
				mensaje_rechazo_comercio.format(nombre),
				''
			)

			bd['comercio'].delete_one({'tipo_id':tipo_id,'num_id':num_id})

	locales = list()
	for l in bd['comercio'].find({'pendiente':1}):
		aux = list(l.values())
		if str(aux[10]) == 'nan': aux[10] = 'N/A'
		if str(aux[11]) == 'nan': aux[11] = 'N/A'
		barrio = bd['barrio'].find_one({'id_barrio':aux[6]})
		aux.append(barrio['municipio'])
		aux.append(barrio['nombre'])
		locales.append(aux)

	return render_template("admin_gestionarSolicitudes_registro_locales.html",locales=locales)


@app.route("/gestionar-solicitudes/registro/entidad-sanitaria",methods=['GET','POST'])
def gestionar_solicitudes_registro_entidad_sanitaria():
	"""
	Retorna la pagina para gestion de solicitudes de
	registro a entidades sanitarias para el usuario
	administrador
	"""
	if 'tipo' not in session or session['tipo'] != 4:
		return redirect(url_for("index"))

	if request.method == 'POST':
		tipo_id = request.form['tipo_id']
		num_id = request.form['num_id']
		correo = request.form['correo']
		nombre = request.form['nombre']
		
		if 'aceptar' in request.form:

			enviar_correo(correo,
				"Solicitud de creacion de cuenta",
				mensaje_aprobacion_entidad_sanitaria.format(nombre),
				''
			)

			bd['entidad_sanitaria'].update_one({
				'tipo_id':tipo_id,
				'num_id':num_id
			},{
				'$set':{
					'pendiente':0
				}
			})

		else:
			enviar_correo(correo,
				"Solicitud de creacion de cuenta",
				mensaje_rechazo_entidad_sanitaria.format(nombre),
				''
			)

			bd['entidad_sanitaria'].delete_one({'tipo_id':tipo_id,'num_id':num_id})

	entidades = list()
	for es in bd['entidad_sanitaria'].find({'pendiente':1}):
		aux = list(es.values())
		barrio = bd['barrio'].find_one({'id_barrio':int(aux[6])})
		aux.append(barrio['municipio'])
		aux.append(barrio['nombre'])
		entidades.append(aux)

	return render_template("admin_gestionarSolicitudes_registro_entidadesSanitarias.html",entidades=entidades)


@app.route("/gestionar-solicitudes/modificacion/civil",methods=['GET','POST'])
def gestionar_solicitudes_modificacion_civil():
	"""
	Retorna la pagina para gestion de solicitudes de
	modificacion a civiles para el usuario administrador
	"""
	if 'tipo' not in session or session['tipo'] != 4:
		return redirect(url_for("index"))
	return render_template("admin_gestionarSolicitudes_modificacion_usuarios.html")


@app.route("/gestionar-solicitudes/modificacion/comercio",methods=['GET','POST'])
def gestionar_solicitudes_modificacion_comercio():
	"""
	Retorna la pagina para gestion de solicitudes de
	modificacion a comercios para el usuario administrador
	"""
	if 'tipo' not in session or session['tipo'] != 4:
		return redirect(url_for("index"))
	return render_template("admin_gestionarSolicitudes_modificacion_locales.html")


@app.route("/gestionar-solicitudes/modificacion/entidad-sanitaria",methods=['GET','POST'])
def gestionar_solicitudes_modificacion_entidad_sanitaria():
	"""
	Retorna la pagina para gestion de solicitudes de
	modificacion a entidades sanitarias para el usuario
	administrador
	"""
	if 'tipo' not in session or session['tipo'] != 4:
		return redirect(url_for("index"))
	return render_template("admin_gestionarSolicitudes_modificacion_entidadesSanitarias.html")


if __name__ == "__main__":
	app.secret_key = "jda()/_s8U9??¡!823jeD" 
	app.run(host='0.0.0.0',port='8080',debug=True)	