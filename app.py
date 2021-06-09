#Framework usado: Flask
from flask import Flask, render_template, redirect, url_for, request, jsonify, flash, session, current_app
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

#Mensajes predefinidos de respuesta automatica
import mensajes

#Usado para generar la contraseña aleatoria
from random import randint,shuffle

#Calculos
from math import ceil

#Niveles de riesgo
niveles = ['muy bajo','bajo','medio','alto','muy alto']

#Formato de fecha
formato_fecha = '%Y-%m-%d %H:%M:%S'

#Cadenas
string_inicio_sesion = "inicio_de_sesion.html"
string_solicitud_creacion = "Solicitud de creacion de cuenta"
string_solicitud_mod = "Solicitud de modificacion de cuenta"
string_solicitud_recuperacion = "Solicitud de recuperacion de contraseña"

#aplicativo flask
app = Flask(__name__)
app.secret_key = "jda()/_s8U9??¡!823jeD" 
#Modulo para encriptacion de contraseñas
bcrypt = Bcrypt(app)
#Coneccion con la base de datos recibida como parametro en el llamado
cliente = MongoClient("mongodb+srv://admin19:admin19@dbcov19.0ih7g.mongodb.net/DBCOV19?retryWrites=true&w=majority")
bd = cliente['projectdb']

usuario_correo = "sistemadegestionyaforo@gmail.com"
contrasena_correo = "ingesoft2020"


def enviar_correo(destino, asunto, mensaje, imagen):
	msj = EmailMessage()
	msj['Subject'] = asunto
	msj['From'] = usuario_correo
	msj['To'] = destino
	msj.set_content(mensaje)

	if len(imagen):
		with current_app.open_resource('QRs/'+imagen+'.png') as img:
			archivo = img.read()
		msj.add_attachment(archivo,maintype='image',subtype='png',filename="Codigo_QR.png")

	with smtplib.SMTP_SSL('smtp.gmail.com',465) as smtp:
		smtp.login(usuario_correo,contrasena_correo)
		smtp.send_message(msj)


def calculo_riesgo_local(acum_riesgo_fechas):
	acum,promedio_dia = 0,0
	for riesgo_dia,personas_dia in acum_riesgo_fechas.values():
		promedio_dia = (riesgo_dia/personas_dia)
		
		if personas_dia >= 100: 
			promedio_dia += 3
		elif  100 > personas_dia >= 50:
			promedio_dia += 2
		elif 50 > personas_dia >= 10:
			promedio_dia += 1
		elif 0 <= personas_dia < 10:
			promedio_dia -= 1

		acum += min(max(promedio_dia,1),10) 

	return acum/len(acum_riesgo_fechas)
	
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

			prueba = list()
			for p in bd['historial_pruebas'].find({'tipo_id_persona':session['tipo_id'],'num_id_persona':session['num_id']}):  
				prueba.append((datetime.strptime(p['fechayhora'], formato_fecha),p['resultado']))

			fecha = None
			dias = 0
			vigente = 0
			if len(prueba):
				prueba = max(prueba, key=lambda x: x[0])
				#Si no se ha hecho una prueba de COVID-19 en los ultimos 15 dias, debe estar en cuarentena
				fecha = prueba[0]
				fecha_min = datetime.today() - timedelta(days=15)
				if prueba[1]=='Positivo' and fecha >= fecha_min: vigente = 1
				if prueba[1]=='Ninguno' and fecha >= fecha_min: vigente = 2
				dias = (fecha - fecha_min).days

			visitas_aux = bd['visita']
			visitas_aux = visitas_aux.find({"ingreso":"SI","tipo_id_persona":session['tipo_id'], "num_id_persona":session['num_id']})
			visitas = list()
			for visita in visitas_aux:
				comercio = bd['comercio'].find({"tipo_id":visita['tipo_id_local'], "num_id":visita['num_id_local']})
				visitas.append((comercio[0]['nombre'],visita['fechayhora']))

			fecha = str(fecha)

			riesgo = niveles[ceil((bd['civil'].find_one({'tipo_id':session['tipo_id'],'num_id':session['num_id']}))['riesgo']/2)-1]
			return render_template("usuario.html", visitas=visitas,vigente=vigente,dias=dias,fecha=fecha,riesgo=riesgo)
		
		if session["tipo"] == 2:
			visitas = list()
			for v in bd['visita'].find({'tipo_id_local':session['tipo_id'], 'num_id_local':session['num_id']}):
				visitas.append((v['tipo_id_persona'],v['num_id_persona'],v['fechayhora'],v['tapabocas'],v['temperatura'],v['ingreso'],(bd['civil'].find_one({'tipo_id':v['tipo_id_persona'],'num_id':v['num_id_persona']})['riesgo'])))

			acum_riesgo_fechas = dict()
			for vis in visitas:
				aux = str(vis[2])[:10] 
				if aux not in acum_riesgo_fechas:
					acum_riesgo_fechas[aux] = [vis[6],1]
				else:
					acum_riesgo_fechas[aux][0] += vis[6]
					acum_riesgo_fechas[aux][1] += 1

			riesgo = niveles[ceil(calculo_riesgo_local(acum_riesgo_fechas)/2)-1] if len(acum_riesgo_fechas) else -1

			return render_template("local.html",visitas=visitas,riesgo=riesgo)

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
			return render_template(string_inicio_sesion)
		else:
			return redirect(url_for("index"))
	else: 
		usuario = request.form['usuario']
		contrasena = request.form['contrasena']
		#Tipos de cuenta: 1: Civil, 2: Comercio, 3: Entidad Sanitaria, 4: admin

		session.clear()
		usuario_bd = bd['civil'].find_one({'usuario':usuario})
		if usuario_bd and bcrypt.check_password_hash(usuario_bd['contrasena'].encode('utf-8'),contrasena.encode('utf-8')):
			if usuario_bd['pendiente'] == 1:
				flash('pendiente')
				return render_template(string_inicio_sesion)
			else:
				session['usuario'] = usuario
				session['tipo'] = 1
				session['tipo_id'] = usuario_bd['tipo_id']
				session['num_id'] = usuario_bd['num_id']
		
		usuario_bd = bd['comercio'].find_one({'usuario':usuario})
		if usuario_bd and bcrypt.check_password_hash(usuario_bd['contrasena'].encode('utf-8'),contrasena.encode('utf-8')):
			if usuario_bd['pendiente'] == 1:
				flash('pendiente')
				return render_template(string_inicio_sesion)
			else:
				session['usuario'] = usuario
				session['tipo'] = 2
				session['tipo_id'] = usuario_bd['tipo_id']
				session['num_id'] = usuario_bd['num_id']
		
		usuario_bd = bd['entidad_sanitaria'].find_one({'usuario':usuario})
		if usuario_bd and bcrypt.check_password_hash(usuario_bd['contrasena'].encode('utf-8'),contrasena.encode('utf-8')):
			if usuario_bd['pendiente'] == 1:
				flash('pendiente')
				return render_template(string_inicio_sesion)
			else:
				session['usuario'] = usuario
				session['tipo'] = 3
				session['tipo_id'] = usuario_bd['tipo_id']
				session['num_id'] = usuario_bd['num_id']
		
		usuario_bd = bd['administrador'].find_one({'usuario':usuario})
		if usuario_bd and usuario_bd['contrasena'] == contrasena:
			session['usuario'] = usuario
			session['tipo'] = 4

		if len(session): return redirect(url_for("index"))
		flash('incorrecto')
		return render_template(string_inicio_sesion)


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
		if request.method == 'POST':
			contrasena_usuario = bd['civil'].find_one({'tipo_id':session['tipo_id'],'num_id':session['num_id']})['contrasena']
			contrasena_actual = request.form['contrasena_act']
			if bcrypt.check_password_hash(contrasena_usuario.encode('utf-8'),contrasena_actual.encode('utf-8')):
				if bd['modificacion'].find_one({'tipo_cuenta':1,'tipo_id':session['tipo_id'],'num_id':session['num_id']}):
					flash('no_solicitud')
				else:
					id_barrio = bd['barrio'].find_one({'nombre':request.form['barrio'],'municipio':request.form['municipio']})['id_barrio']
					contrasena = "" if 'contrasena' not in request.form else (bcrypt.generate_password_hash(request.form['contrasena'].encode('utf-8'))).decode('utf-8')
					bd['modificacion'].insert_one({
						'tipo_cuenta':1,
						'recuperar':0,
						'tipo_id':session['tipo_id'],
						'num_id': session['num_id'],
						'nombres':request.form['nombres'],
						'apellidos':request.form['apellidos'],
						'genero':request.form['genero'],
						'nacimiento':request.form['nacimiento'],
						'id_barrio':id_barrio,
						'direccion':request.form['direccion'],
						'correo':request.form['correo'],
						'telefono':(request.form['telefono']),
						'contrasena_nueva':contrasena
					})
					flash('correcto')
					return redirect(url_for("index"))


			else:
				flash('no_contrasena')

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
		departamentos.sort()
		return render_template('usuario_cuenta.html',usuario=usuario,barrio=barrio,departamentos=departamentos)

	
	elif session['tipo'] == 2:
		if request.method == 'POST':
			contrasena_usuario = bd['comercio'].find_one({'tipo_id':session['tipo_id'],'num_id':session['num_id']})['contrasena']
			contrasena_actual = request.form['contrasena_act']
			if bcrypt.check_password_hash(contrasena_usuario.encode('utf-8'),contrasena_actual.encode('utf-8')):
				if bd['modificacion'].find_one({'tipo_cuenta':2,'tipo_id':session['tipo_id'],'num_id':session['num_id']}):
					flash('no_solicitud')
				else:
					id_barrio = bd['barrio'].find_one({'nombre':request.form['barrio'],'municipio':request.form['municipio']})['id_barrio']
					contrasena = "" if 'contrasena' not in request.form else (bcrypt.generate_password_hash(request.form['contrasena'].encode('utf-8'))).decode('utf-8')
					tel1 = (request.form['telefono1'])
					tel2 = nan if 'telefono2' not in request.form else (request.form['telefono2'])
					tel3 = nan if 'telefono3' not in request.form else (request.form['telefono3'])
					bd['modificacion'].insert_one({
						'tipo_cuenta':2,
						'recuperar':0,
						'tipo_id': session['tipo_id'],
						'num_id': session['num_id'],
						'nombre':request.form['nombre'],
						'id_barrio':id_barrio,
						'correo':request.form['correo'],
						'categoria':request.form['categoria'],
						'telefono1':tel1,
						'telefono2':tel2,
						'telefono3':tel3,
						'contrasena_nueva':contrasena
					})
					flash('correcto')
					return redirect(url_for("index"))

			else:
				flash('no_contrasena')

		local = list(bd['comercio'].find_one({
			'tipo_id':session['tipo_id'],
			'num_id':session['num_id']
		}).values())

		barrio = list(bd['barrio'].find_one({
			'id_barrio':local[6]
		}).values())

		telefonos = 1
		if str(local[10]) != 'nan': telefonos = 2
		if str(local[11]) != 'nan': telefonos = 3
		local.append(telefonos)

		departamentos = list()
		dep = bd['departamento'].find({})
		for u in dep:
			departamentos.append(u['nombre'])

		categorias = list()
		cat = bd['categoria'].find({})
		for u in cat:
			categorias.append(u['nombre'])
		departamentos.sort()
		return render_template('local_cuenta.html',local=local,barrio=barrio,departamentos=departamentos,categorias=categorias)
	
	elif session['tipo'] == 3:
		if request.method == 'POST':
			contrasena_usuario = bd['entidad_sanitaria'].find_one({'tipo_id':session['tipo_id'],'num_id':session['num_id']})['contrasena']
			contrasena_actual = request.form['contrasena_act']
			if bcrypt.check_password_hash(contrasena_usuario.encode('utf-8'),contrasena_actual.encode('utf-8')):
				if bd['modificacion'].find_one({'tipo_cuenta':3,'tipo_id':session['tipo_id'],'num_id':session['num_id']}):
					flash('no_solicitud')
				else:
					id_barrio = bd['barrio'].find_one({'nombre':request.form['barrio'],'municipio':request.form['municipio']})['id_barrio']
					contrasena = "" if 'contrasena' not in request.form else (bcrypt.generate_password_hash(request.form['contrasena'].encode('utf-8'))).decode('utf-8')
					bd['modificacion'].insert_one({
						'tipo_cuenta':3,
						'recuperar':0,
						'tipo_id':session['tipo_id'],
						'num_id': session['num_id'],
						'nombre':request.form['nombre'],
						'id_barrio':id_barrio,
						'correo':request.form['correo'],
						'telefono':request.form['telefono'],
						'contrasena_nueva':contrasena
					})
					flash('correcto')
					return redirect(url_for("index"))

			else:
				flash('no_contrasena')

		entidad = list(bd['entidad_sanitaria'].find_one({
			'tipo_id':session['tipo_id'],
			'num_id':session['num_id']
		}).values())

		barrio = list(bd['barrio'].find_one({
			'id_barrio':int(entidad[6])
		}).values())

		departamentos = list()
		dep = bd['departamento'].find({})
		for u in dep:
			departamentos.append(u['nombre'])
		departamentos.sort()
		return render_template('entidad_sanitaria_cuenta.html',entidad=entidad,barrio=barrio,departamentos=departamentos)
	
	elif session['tipo'] == 4:
		if request.method == 'POST':
			bd['administrador'].update_one({
				'usuario':session['usuario']
			},{
				'$set':{
					'contrasena':request.form['contrasena'],
					'nombres':request.form['nombres'],
					'apellidos':request.form['apellidos']
				}
			})
			flash('correcto')
			return redirect(url_for("index"))

		adminn = list(bd['administrador'].find_one({
			'usuario':session['usuario']
		}).values())

		return render_template('admin_cuenta.html',adminn=adminn)


@app.route("/cerrar-sesion/")
def cerrar_sesion():
	"""
	Cierra la sesion en cuestion y redirecciona al menu
	principal
	"""
	session.clear()
	return redirect(url_for("index"))

def calculo_riesgo_registro(riesgo_barrio,edad):
	"""
	Retorna el calculo del riesgo para el registro
	de usuarios dependiendo del riesgo del barrio
	en el que vive y su edad.
	"""
	riesgo_edad = 0
	if 14<=edad<=19 or 30<=edad<=35: riesgo_edad = 1
	elif 20<=edad<30: riesgo_edad = 2
	elif edad >= 60: riesgo_edad = -1
	riesgo = min(max(riesgo_barrio + riesgo_edad,1),10)

	return riesgo

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
		departamentos.sort()
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
		
		barrio_aux = bd['barrio'].find({'nombre':barrio,'municipio':municipio})[0]
		id_barrio = barrio_aux['id_barrio']
		riesgo_barrio = barrio_aux['riesgo']

		direccion = request.form['direccion']
		correo = request.form['correo']
		telefono = (request.form['telefono'])
		usuario = request.form['usuario']
		contrasena = (bcrypt.generate_password_hash(request.form['contrasena'].encode('utf-8'))).decode('utf-8')

		edad = ((datetime.now() - datetime.strptime(nacimiento, '%Y-%m-%d')).days)//365

		riesgo = calculo_riesgo_registro(riesgo_barrio,edad)

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
			'pendiente':1,
			'riesgo':riesgo
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
		departamentos.sort()
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
		telefono1 = (request.form['telefono1'])
		telefono2, telefono3 = nan,nan
		if telefonos > 1: telefono2 = (request.form['telefono2'])
		if telefonos > 2: telefono3 = (request.form['telefono3'])
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

		departamentos.sort()
		return render_template("entidad_sanitaria_registro.html", departamentos=departamentos)
	else:
		tipo_id = request.form['tipo_id']
		num_id = request.form['num_id']
		nombre = request.form['nombre']
		
		municipio = request.form['municipio']
		barrio = request.form['barrio']

		id_barrio = bd['barrio'].find({'nombre':barrio,'municipio':municipio})[0]['id_barrio']

		correo = request.form['correo']
		telefono = (request.form['telefono'])
		
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

@app.route("/recuperar-contrasena/",methods=["GET","POST"])
def recuperar_contrasena():
	if'tipo' in session:
		return redirect(url_for("index"))

	if request.method == 'POST':
		formulario = int(request.form['tipo_form'])
		if formulario == 1:
			tipo_id = request.form['tipo_id']
			num_id = request.form['num_id']
			nombres = request.form['nombres']
			apellidos = request.form['apellidos']
			genero = request.form['genero']
			nacimiento = request.form['nacimiento']

			departamento = request.form['departamento']
			municipio = request.form['municipio']
			barrio = request.form['barrio']
			id_barrio = bd['barrio'].find_one({'nombre':barrio,'municipio':municipio,'departamento':departamento})['id_barrio']
			
			direccion = request.form['direccion']
			correo = request.form['correo']
			telefono = request.form['telefono']
			usuario = request.form['usuario']

			if bd['civil'].find_one({'tipo_id':tipo_id,'num_id':num_id,'usuario':usuario}):
				if bd['modificacion'].find_one({'tipo_id':tipo_id,'num_id':num_id}):
					flash('pendiente')
				else:
					bd['modificacion'].insert_one({
						'tipo_cuenta':1,
						'recuperar':1,
						'tipo_id':tipo_id,
						'num_id': num_id,
						'nombres':nombres,
						'apellidos':apellidos,
						'genero':genero,
						'nacimiento':nacimiento,
						'id_barrio':id_barrio,
						'direccion':direccion,
						'correo':correo,
						'telefono':telefono,
						'contrasena_nueva':''
					})
					flash('correcto')
					return redirect(url_for("inicio_sesion"))
			else:
				flash('no_usuario_id')

		elif formulario == 2:
			tipo_id = request.form['tipo_id']
			num_id = request.form['num_id']
			nombre = request.form['nombre']
			
			departamento = request.form['departamento']
			municipio = request.form['municipio']
			barrio = request.form['barrio']
			id_barrio = bd['barrio'].find_one({'nombre':barrio,'municipio':municipio,'departamento':departamento})['id_barrio']
			
			correo = request.form['correo']
			categoria = request.form['categoria']
			telefono1 = request.form['telefono1']
			telefono2 = nan if 'telefono2' not in request.form else (request.form['telefono2'])
			telefono3 = nan if 'telefono3' not in request.form else (request.form['telefono3'])
			usuario = request.form['usuario']
			if bd['comercio'].find_one({'tipo_id':tipo_id,'num_id':num_id,'usuario':usuario}):
				if bd['modificacion'].find_one({'tipo_id':tipo_id,'num_id':num_id}):
					flash('pendiente')
				else:
					
					bd['modificacion'].insert_one({
						'tipo_cuenta':2,
						'recuperar':1,
						'tipo_id': tipo_id,
						'num_id': num_id,
						'nombre':nombre,
						'id_barrio':id_barrio,
						'correo':correo,
						'categoria':categoria,
						'telefono1':telefono1,
						'telefono2':telefono2,
						'telefono3':telefono3,
						'contrasena_nueva':''
					})
					flash('correcto')
					return redirect(url_for("inicio_sesion"))
			else:
				flash('no_usuario_id')

		elif formulario == 3:
			tipo_id = request.form['tipo_id']
			num_id = request.form['num_id']
			nombre = request.form['nombre']

			departamento = request.form['departamento']
			municipio = request.form['municipio']
			barrio = request.form['barrio']
			id_barrio = bd['barrio'].find_one({'nombre':barrio,'municipio':municipio,'departamento':departamento})['id_barrio']
			
			correo = request.form['correo']
			telefono = request.form['telefono']
			usuario = request.form['usuario']

			if bd['entidad_sanitaria'].find_one({'tipo_id':tipo_id,'num_id':num_id,'usuario':usuario}):
				if bd['modificacion'].find_one({'tipo_id':tipo_id,'num_id':num_id}):
					flash('pendiente')
				else:
					
					bd['modificacion'].insert_one({
						'tipo_cuenta':3,
						'recuperar':1,
						'tipo_id':tipo_id,
						'num_id': num_id,
						'nombre':nombre,
						'id_barrio':id_barrio,
						'correo':correo,
						'telefono':telefono,
						'contrasena_nueva':''
					})
					flash('correcto')
					return redirect(url_for("inicio_sesion"))
			else:
				flash('no_usuario_id')
			

	departamentos = list()
	dep = bd['departamento'].find({})
	for u in dep:
		departamentos.append(u['nombre'])

	categorias = list()
	cat = bd['categoria'].find({})
	for u in cat:
		categorias.append(u['nombre'])

		departamentos.sort()
	return render_template("recuperar_contrasena.html",departamentos=departamentos,categorias=categorias)


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
def local_qr():
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
			prueba.append((datetime.strptime(p['fechayhora'], formato_fecha),p['resultado']))

		permitido = 1
		if len(prueba):
			prueba = max(prueba, key=lambda x: x[0])
			#Si no se ha hecho una prueba de COVID-19 en los ultimos 15 dias, debe estar en cuarentena
			fecha = prueba[0]
			fecha_min = datetime.today() - timedelta(days=15)
			if prueba[1]!='Negativo' and fecha >= fecha_min: permitido = 0

		tapabocas = 'SI'
		if 'tapabocas' not in request.form:
			permitido = 0
			tapabocas = 'NO'

		if not 35<=float(request.form['temp'])<38: permitido = 0

		if permitido: ingreso = 'SI'
		else: ingreso = 'NO'

		fechayhora = datetime.fromtimestamp(time()).strftime(formato_fecha)
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
def local_no_qr():
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
			prueba.append((datetime.strptime(p['fechayhora'], formato_fecha),p['resultado']))

		permitido = 1
		if len(prueba):
			prueba = max(prueba, key=lambda x: x[0])
			#Si no se ha hecho una prueba de COVID-19 en los ultimos 15 dias, debe estar en cuarentena
			fecha = prueba[0]
			fecha_min = datetime.today() - timedelta(days=15)
			if prueba[1]!='Negativo' and fecha >= fecha_min: permitido = 0

		tapabocas = 'SI'
		if 'tapabocas' not in request.form:
			permitido = 0
			tapabocas = 'NO'

		if not 35<=float(request.form['temp'])<38: permitido = 0

		if permitido: ingreso = 'SI'
		else: ingreso = 'NO'

		fechayhora = datetime.fromtimestamp(time()).strftime(formato_fecha)
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

		fechayhora = datetime.strptime(request.form['fecha']+' '+request.form['hora']+':00', formato_fecha)
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

		fechayhora = datetime.fromtimestamp(time()).strftime(formato_fecha)
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


@app.route("/entidad-sanitaria/usuarios/",methods=['GET'])
def entidad_sanitaria_usuarios():
	"""
	Retorna pagina donde se listan los usuarios
	registrados en el sistema para las entidades
	sanitarias
	"""
	if 'tipo' not in session or session['tipo'] != 3:
		return redirect(url_for("index"))

	usuarios = list()
	for l in bd['civil'].find({'pendiente':0}):
		aux = list(l.values())
		barrio = bd['barrio'].find_one({'id_barrio':aux[9]})
		aux.append(barrio['municipio'])
		aux.append(barrio['nombre'])
		usuarios.append(aux)

	return render_template('entidad_sanitaria_usuarios.html',usuarios=usuarios)


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

	categorias = list()
	cat = bd['categoria'].find({})
	for u in cat:
		categorias.append(u['nombre'])

	return render_template("admin_gestionarLocales.html",locales=locales,categorias=categorias)


@app.route("/gestionar-entidades-sanitarias/",methods=['GET','POST'])
def gestionar_entidades_sanitarias():
	"""
	Retorna la pagina de gestion de entidades de salud
	para el usuario administrador
	"""
	if 'tipo' not in session or session['tipo'] != 4:
		return redirect(url_for("index"))

	if request.method == 'POST':
		bd['entidad_sanitaria'].update_one({
			'tipo_id':request.form['tipo_id'],
			'num_id':request.form['num_id']
		},{
			'$set':{
				'nombre':request.form['nombre'],
				'correo':request.form['correo'],
				'telefono':request.form['telefono']
			}
		})

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

	barrios = set()
	departamentos = set()
	usuarios = list()
	for l in bd['civil'].find({'pendiente':0}):
		aux = list(l.values())
		barrio = bd['barrio'].find_one({'id_barrio':aux[9]})
		aux.append(barrio['municipio'])
		aux.append(barrio['nombre'])
		aux.append(barrio['departamento'])
		aux.append('No')
		barrios.add(aux[16])
		departamentos.add(aux[17])
		prueba = list()
		for p in bd['historial_pruebas'].find({'tipo_id_persona':aux[1],'num_id_persona':aux[2]}):  
			prueba.append((datetime.strptime(p['fechayhora'], formato_fecha),p['resultado']))

		if len(prueba):
			prueba = max(prueba, key=lambda x: x[0])
			#Si no se ha hecho una prueba de COVID-19 en los ultimos 15 dias, debe estar en cuarentena
			fecha = prueba[0]
			fecha_min = datetime.today() - timedelta(days=15)
			if prueba[1]=='Positivo' and fecha >= fecha_min: aux[18] = 'Si'
		
		usuarios.append(aux)
			
	return render_template("admin_gestionarUsuarios.html",usuarios=usuarios,barrios=list(barrios),departamentos=list(departamentos))


@app.route("/gestionar-visitas/")
def gestionar_visitas():
	"""
	Retorna la pagina de gestion de civiles
	para el usuario administrador
	"""
	if 'tipo' not in session or session['tipo'] != 4:
		return redirect(url_for("index"))

	visitas = list()
	for l in bd['visita'].find({}):
		aux = list(l.values())
		usuario = bd['civil'].find_one({'tipo_id':aux[1],'num_id':aux[2]})
		aux.append(usuario['nombres'])
		aux.append(usuario['apellidos'])
		aux.append(bd['comercio'].find_one({'tipo_id':aux[4],'num_id':aux[5]})['nombre'])
		visitas.append(aux)

	return render_template("admin_gestionarVisitas.html",visitas=visitas)


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
				'departamento':request.form['departamento'],
				'riesgo':int(request.form['riesgo1'])
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
	for b in bd['barrio'].find({}):
		barrio_aux = list(b.values())
		barrio_aux[5] = niveles[ceil(barrio_aux[5]/2)-1]
		barrios.append(barrio_aux)

	departamentos.sort()
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
				string_solicitud_creacion,
				mensajes.mensaje_aprobacion_civil.format(nombre),
				tipo_id+'-'+num_id
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
				string_solicitud_creacion,
				mensajes.mensaje_rechazo_civil.format(nombre),
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
				string_solicitud_creacion,
				mensajes.mensaje_aprobacion_comercio.format(nombre),
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
				string_solicitud_creacion,
				mensajes.mensaje_rechazo_comercio.format(nombre),
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
				string_solicitud_creacion,
				mensajes.mensaje_aprobacion_entidad_sanitaria.format(nombre),
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
				string_solicitud_creacion,
				mensajes.mensaje_rechazo_entidad_sanitaria.format(nombre),
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

	if request.method == 'POST':
		tipo_id = request.form['tipo_id']
		num_id = request.form['num_id']
		correo_1 = bd['civil'].find_one({'tipo_id':tipo_id,'num_id':num_id})['correo']
		correo_2 = request.form['correo']
		nombre = request.form['nombre']

		usuario = list(bd['modificacion'].find_one({'tipo_cuenta':1,'tipo_id':tipo_id,'num_id':num_id}).values())
		
		if 'aceptar' in request.form:

			if usuario[2] == 0:

				bd['civil'].update_one({
					'tipo_id':tipo_id,
					'num_id':num_id
				},{
					'$set':{
						'nombres':usuario[5],
						'apellidos':usuario[6],
						'genero':usuario[7],
						'nacimiento':usuario[8],
						'id_barrio':usuario[9],
						'direccion':usuario[10],
						'correo':usuario[11],
						'telefono':usuario[12]
					}
				})

				if len(usuario[13]): bd['civil'].update_one({'tipo_id':tipo_id,'num_id':num_id},{'$set':{'contrasena':usuario[13]}})
				
				enviar_correo(correo_1,
					string_solicitud_mod,
					mensajes.mensaje_aprobacion_mod_civil.format(nombre),
					'')
				if correo_1 != correo_2:
					enviar_correo(correo_2,
						string_solicitud_mod,
						mensajes.mensaje_aprobacion_mod_civil.format(nombre),
						'')
			else:
				aux_contrasena = list()
				aux_contrasena.append(chr(randint(65,90)))
				aux_contrasena.append(chr(randint(97,122)))
				aux_contrasena.append(chr(randint(48,57)))
				aux_contrasena.append(chr(randint(58,64)))
				for _ in range(randint(6,11)):
					aux_contrasena.append(chr(randint(48,90)))

				shuffle(aux_contrasena)
				contrasena_tmp = ''.join(aux_contrasena)

				contrasena = (bcrypt.generate_password_hash(contrasena_tmp.encode('utf-8'))).decode('utf-8')

				bd['civil'].update_one({
					'tipo_id':tipo_id,
					'num_id':num_id
				},{
					'$set':{
						'contrasena':contrasena
					}
				})

				enviar_correo(correo_1,
					string_solicitud_recuperacion,
					mensajes.mensaje_aprobacion_cambio_contrasena.format(nombre,contrasena_tmp),
					'')

		else:

			if usuario[2] == 0:
				enviar_correo(correo_1,
					string_solicitud_mod,
					mensajes.mensaje_rechazo_mod_civil.format(nombre),
					'')
			else:
				enviar_correo(correo_1,
					string_solicitud_recuperacion,
					mensajes.mensaje_rechazo_cambio_contrasena.format(nombre),
					'')

		bd['modificacion'].delete_one({'tipo_cuenta':1,'tipo_id':tipo_id,'num_id':num_id})
			

	usuarios = list()
	for l in bd['modificacion'].find({'tipo_cuenta':1}):
		aux = list(l.values())
		barrio = bd['barrio'].find_one({'id_barrio':aux[9]})
		if len(aux[13]): aux.append('SI')
		else: aux.append('NO')
		aux.append(barrio['municipio'])
		aux.append(barrio['nombre'])
		if aux[2]: aux[2] = 'SI'; aux[14] = 'SI'
		else: aux[2] = 'NO'
		usuarios.append(aux)

	return render_template("admin_gestionarSolicitudes_modificacion_usuarios.html",usuarios=usuarios)


@app.route("/gestionar-solicitudes/modificacion/comercio",methods=['GET','POST'])
def gestionar_solicitudes_modificacion_comercio():
	"""
	Retorna la pagina para gestion de solicitudes de
	modificacion a comercios para el usuario administrador
	"""
	if 'tipo' not in session or session['tipo'] != 4:
		return redirect(url_for("index"))

	if request.method == 'POST':
		tipo_id = request.form['tipo_id']
		num_id = request.form['num_id']
		correo_1 = bd['comercio'].find_one({'tipo_id':tipo_id,'num_id':num_id})['correo']
		correo_2 = request.form['correo']
		nombre = request.form['nombre']

		local = list(bd['modificacion'].find_one({'tipo_cuenta':2,'tipo_id':tipo_id,'num_id':num_id}).values())
		
		if 'aceptar' in request.form:

			if local[2] == 0:

				bd['comercio'].update_one({
					'tipo_id':tipo_id,
					'num_id':num_id
				},{
					'$set':{
						'nombre':local[5],
						'id_barrio':local[6],
						'correo':local[7],
						'categoria':local[8],
						'telefono1':local[9],
						'telefono2':local[10],
						'telefono3':local[11]
					}
				})

				if len(local[12]): bd['comercio'].update_one({'tipo_id':tipo_id,'num_id':num_id},{'$set':{'contrasena':local[12]}})
				
				enviar_correo(correo_1,
					string_solicitud_mod,
					mensajes.mensaje_aprobacion_mod_comercio.format(nombre),
					'')
				if correo_1 != correo_2:
					enviar_correo(correo_2,
						string_solicitud_mod,
						mensajes.mensaje_aprobacion_mod_comercio.format(nombre),
						'')
			else:
				aux_contrasena = list()
				aux_contrasena.append(chr(randint(65,90)))
				aux_contrasena.append(chr(randint(97,122)))
				aux_contrasena.append(chr(randint(48,57)))
				aux_contrasena.append(chr(randint(58,64)))
				for _ in range(randint(6,11)):
					aux_contrasena.append(chr(randint(48,90)))

				shuffle(aux_contrasena)
				contrasena_tmp = ''.join(aux_contrasena)

				contrasena = (bcrypt.generate_password_hash(contrasena_tmp.encode('utf-8'))).decode('utf-8')

				bd['comercio'].update_one({
					'tipo_id':tipo_id,
					'num_id':num_id
				},{
					'$set':{
						'contrasena':contrasena
					}
				})

				enviar_correo(correo_1,
					string_solicitud_recuperacion,
					mensajes.mensaje_aprobacion_cambio_contrasena.format(nombre,contrasena_tmp),
					'')

		else:
			if local[2] == 0:
				enviar_correo(correo_1,
					string_solicitud_mod,
					mensajes.mensaje_rechazo_mod_comercio.format(nombre),
					'')
			else:
				enviar_correo(correo_1,
					string_solicitud_recuperacion,
					mensajes.mensaje_rechazo_cambio_contrasena.format(nombre),
					'')

		bd['modificacion'].delete_one({'tipo_cuenta':2,'tipo_id':tipo_id,'num_id':num_id})

	locales = list()
	for l in bd['modificacion'].find({'tipo_cuenta':2}):
		aux = list(l.values())
		if str(aux[10]) == 'nan': aux[10] = 'N/A'
		if str(aux[11]) == 'nan': aux[11] = 'N/A'
		if len(aux[12]): aux.append('SI')
		else: aux.append('NO')
		barrio = bd['barrio'].find_one({'id_barrio':aux[6]})
		aux.append(barrio['municipio'])
		aux.append(barrio['nombre'])
		if aux[2]: aux[2] = 'SI'; aux[13] = 'SI'
		else: aux[2] = 'NO'
		locales.append(aux)

	return render_template("admin_gestionarSolicitudes_modificacion_locales.html",locales=locales)


@app.route("/gestionar-solicitudes/modificacion/entidad-sanitaria",methods=['GET','POST'])
def gestionar_solicitudes_modificacion_entidad_sanitaria():
	"""
	Retorna la pagina para gestion de solicitudes de
	modificacion a entidades sanitarias para el usuario
	administrador
	"""
	if 'tipo' not in session or session['tipo'] != 4:
		return redirect(url_for("index"))

	if request.method == 'POST':
		tipo_id = request.form['tipo_id']
		num_id = request.form['num_id']
		correo_1 = bd['entidad_sanitaria'].find_one({'tipo_id':tipo_id,'num_id':num_id})['correo']
		correo_2 = request.form['correo']
		nombre = request.form['nombre']

		entidad = list(bd['modificacion'].find_one({'tipo_cuenta':3,'tipo_id':tipo_id,'num_id':num_id}).values())
		
		if 'aceptar' in request.form:

			if entidad[2] == 0:

				bd['entidad_sanitaria'].update_one({
					'tipo_id':tipo_id,
					'num_id':num_id
				},{
					'$set':{
						'nombre':entidad[5],
						'id_barrio':entidad[6],
						'correo':entidad[7],
						'telefono':entidad[8]
					}
				})

				if len(entidad[9]): bd['entidad_sanitaria'].update_one({'tipo_id':tipo_id,'num_id':num_id},{'$set':{'contrasena':entidad[9]}})
				
				enviar_correo(correo_1,
					string_solicitud_mod,
					mensajes.mensaje_aprobacion_mod_entidad_sanitaria.format(nombre),
					'')
				if correo_1 != correo_2:
					enviar_correo(correo_2,
						string_solicitud_mod,
						mensajes.mensaje_aprobacion_mod_entidad_sanitaria.format(nombre),
						'')

			else:
				aux_contrasena = list()
				aux_contrasena.append(chr(randint(65,90)))
				aux_contrasena.append(chr(randint(97,122)))
				aux_contrasena.append(chr(randint(48,57)))
				aux_contrasena.append(chr(randint(58,64)))
				for _ in range(randint(6,11)):
					aux_contrasena.append(chr(randint(48,90)))

				shuffle(aux_contrasena)
				contrasena_tmp = ''.join(aux_contrasena)

				contrasena = (bcrypt.generate_password_hash(contrasena_tmp.encode('utf-8'))).decode('utf-8')

				bd['entidad_sanitaria'].update_one({
					'tipo_id':tipo_id,
					'num_id':num_id
				},{
					'$set':{
						'contrasena':contrasena
					}
				})

				enviar_correo(correo_1,
					string_solicitud_recuperacion,
					mensajes.mensaje_aprobacion_cambio_contrasena.format(nombre,contrasena_tmp),
					'')
		else:

			if entidad[2] == 0:
				enviar_correo(correo_1,
					string_solicitud_mod,
					mensajes.mensaje_rechazo_mod_comercio.format(nombre),
					'')

			else:
				enviar_correo(correo_1,
					string_solicitud_recuperacion,
					mensajes.mensaje_rechazo_cambio_contrasena.format(nombre),
					'')

		bd['modificacion'].delete_one({'tipo_cuenta':3,'tipo_id':tipo_id,'num_id':num_id})

	entidades = list()
	for es in bd['modificacion'].find({'tipo_cuenta':3}):
		aux = list(es.values())
		if len(aux[9]): aux.append('SI')
		else: aux.append('NO')
		barrio = bd['barrio'].find_one({'id_barrio':aux[6]})
		aux.append(barrio['municipio'])
		aux.append(barrio['nombre'])
		if aux[2]: aux[2] = 'SI'; aux[10] = 'SI'
		else: aux[2] = 'NO'
		entidades.append(aux)

	return render_template("admin_gestionarSolicitudes_modificacion_entidadesSanitarias.html",entidades=entidades)


@app.before_request
def recargar_sesion():
	session.permanent = True
	app.permanent_session_lifetime = timedelta(minutes=15)


if __name__ == "__main__":
	app.run(host='localhost',port='8080',debug=True)