#Framework usado: Flask
from flask import Flask, render_template, redirect, url_for, request, jsonify, flash, session
from flask_bcrypt import Bcrypt

#Analisis de imagenes con codigos QR
from pyzbar.pyzbar import decode
from PIL import Image

#Manejo de tiempos
from datetime import date,timedelta,datetime
from time import time

#Libreria para conexion con la base de datos
import pymysql

#aplicativo flask
app = Flask(__name__)
#Modulo para encriptacion de contraseñas
bcrypt = Bcrypt(app)
#Coneccion con la base de datos
connection = pymysql.connect(
		host='localhost', #ip
		user='root',
		password='',
		db=''
	)


@app.route("/")
def index():
	"""
	Pagina principal, si no se ha iniciado una sesion, se
	muestra el menu principal de la pagina, de lo contrario
	se muestran los distintos menus dependiendo del tipo de
	cuenta en sesion

	"""
	if "tipo" in session:
		cursor = connection.cursor()

		if session["tipo"] == 1:
			sql = "SELECT nombre,fechayhora FROM (test.comercio  INNER JOIN test.visita ON(tipo_id_persona = '{}' AND num_id_persona = {} AND tipo_id = tipo_id_local AND num_id = num_id_local))".format(session['tipo_id'],session['num_id'])
			cursor.execute(sql)
			visitas = cursor.fetchall()
			return render_template("usuario.html", visitas=visitas)
		
		if session["tipo"] == 2:
			sql = "SELECT tipo_id_persona,num_id_persona,fechayhora,tapabocas,temperatura,ingreso FROM test.visita WHERE(tipo_id_local = '{}' AND num_id_local = {})".format(session['tipo_id'],session['num_id'])
			cursor.execute(sql)
			visitas = cursor.fetchall()
			
			return render_template("local.html",visitas=visitas)

		if session["tipo"] == 3:
			sql = "SELECT id_historial,tipo_id_persona,num_id_persona,fechayhora,resultado FROM test.historial_pruebas WHERE(tipo_id_entidad = '{}' AND num_id_entidad = {})".format(session['tipo_id'],session['num_id'])
			cursor.execute(sql)
			pruebas = cursor.fetchall()

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
	
	cursor = connection.cursor()
	
	if request.method =='GET':
		return render_template("inicio_de_sesion.html")
	else: 
		usuario = request.form['usuario']
		contrasena = request.form['contrasena']
		tipo_cuenta = 0 # 1: Civil, 2: Comercio, 3: Entidad Sanitaria, 4: admin

		sql1 = "SELECT usuario,contrasena,pendiente,tipo_id,num_id FROM test.civil WHERE('{}' = usuario)".format(usuario)
		sql2 = "SELECT usuario,contrasena,pendiente,tipo_id,num_id FROM test.comercio WHERE('{}' = usuario)".format(usuario)
		sql3 = "SELECT usuario,contrasena,pendiente,tipo_id,num_id FROM test.entidad_sanitaria WHERE('{}' = usuario)".format(usuario)
		sql4 = "SELECT usuario,contrasena FROM test.administrador WHERE('{}' = usuario)".format(usuario)
		
		cursor.execute(sql1)
		user = cursor.fetchall()
		print(user)
		if len(user):
			if bcrypt.check_password_hash(user[0][1].encode('utf-8'),contrasena.encode('utf-8')):
				if user[0][2] == 1:
					flash('pendiente')
					return render_template("inicio_de_sesion.html")
				else:
					session['usuario'] = usuario
					session['tipo'] = 1
					session['tipo_id'] = user[0][3]
					session['num_id'] = user[0][4]
		
		cursor.execute(sql2)
		user = cursor.fetchall()
		if len(user):
			if bcrypt.check_password_hash(user[0][1].encode('utf-8'),contrasena.encode('utf-8')):
				if user[0][2] == 1:
					flash('pendiente')
					return render_template("inicio_de_sesion.html")
				else:
					session['usuario'] = usuario
					session['tipo'] = 2
					session['tipo_id'] = user[0][3]
					session['num_id'] = user[0][4]
		
		cursor.execute(sql3)
		user = cursor.fetchall()
		if len(user):
			if bcrypt.check_password_hash(user[0][1].encode('utf-8'),contrasena.encode('utf-8')):
				if user[0][2] == 1:
					flash('pendiente')
					return render_template("inicio_de_sesion.html")
				else:
					session['usuario'] = usuario
					session['tipo'] = 3
					session['tipo_id'] = user[0][3]
					session['num_id'] = user[0][4]
		
		cursor.execute(sql4)
		user = cursor.fetchall()
		if len(user):
			if bcrypt.check_password_hash(user[0][1].encode('utf-8'),contrasena.encode('utf-8')):
				session['usuario'] = usuario
				session['tipo'] = 4
		
		if len(session): return redirect(url_for("index"))
		flash('incorrecto')
		return render_template("inicio_de_sesion.html")

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
	
	cursor = connection.cursor()

	if request.method == 'GET':
		sql = "SELECT nombre FROM test.departamento"
		cursor.execute(sql)
		departamentos = cursor.fetchall()

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
		sql = "SELECT id_barrio FROM test.barrio WHERE(nombre = '{}' AND municipio = '{}')".format(barrio,municipio)
		cursor.execute(sql)
		id_barrio = cursor.fetchall()[0][0]

		direccion = request.form['direccion']
		correo = request.form['correo']
		telefono = request.form['telefono']
		usuario = request.form['usuario']
		contrasena = (bcrypt.generate_password_hash(request.form['contrasena'].encode('utf-8'))).decode('utf-8')
		
		sql = "INSERT INTO test.civil VALUES('{}',{},'{}','{}','{}','{}','{}','{}',{},'{}','{}',{},{})".format(tipo_id,num_id,usuario,contrasena,nombres,apellidos,genero,nacimiento,id_barrio,direccion,correo,telefono,1)
		cursor.execute(sql)
		connection.commit()
		
		flash('registro')
		return redirect(url_for("index"))


@app.route("/registro-local/",methods=["GET","POST"])
def registro_local():
	"""
	Retorna formulario para registro de locales e
	inscribe los locales en la base de datos como
	pendientes de aceptacion.
	"""

	cursor = connection.cursor()

	if request.method == 'GET':
		sql = "SELECT nombre FROM test.departamento"
		cursor.execute(sql)
		departamentos = cursor.fetchall()

		sql = "SELECT nombre FROM test.categoria"
		cursor.execute(sql)
		categorias = cursor.fetchall()

		return render_template("local_registro.html", departamentos=departamentos,categorias=categorias)
	else:
		tipo_id = request.form['tipo_id']
		num_id = request.form['num_id']
		nombre = request.form['nombre']
		
		municipio = request.form['municipio']
		barrio = request.form['barrio']
		sql = "SELECT id_barrio FROM test.barrio WHERE(nombre = '{}' AND municipio = '{}')".format(barrio,municipio)
		cursor.execute(sql)
		id_barrio = cursor.fetchall()[0][0]

		correo = request.form['correo']
		categoria = request.form['categoria']
		telefonos = int(request.form['telefonos'])
		telefono1 = request.form['telefono1']
		telefono2, telefono3 = "NULL","NULL"
		if telefonos > 1: telefono2 = request.form['telefono2']
		if telefonos > 2: telefono3 = request.form['telefono3']
		usuario = request.form['usuario']
		contrasena = (bcrypt.generate_password_hash(request.form['contrasena'].encode('utf-8'))).decode('utf-8')
		
		sql = "INSERT INTO test.comercio VALUES('{}',{},'{}','{}','{}',{},'{}','{}',{},{},{},{})".format(tipo_id,num_id,usuario,contrasena,nombre,id_barrio,correo,categoria,telefono1,telefono2,telefono3,1)
		cursor.execute(sql)
		connection.commit()
		
		flash('registro')
		return redirect(url_for("index"))


@app.route("/registro-entidad-salud/",methods=["GET","POST"])
def registro_entidad_salud():
	"""
	Retorna formulario para registro de entidades de
	salud inscribe los entidades de salud en la base
	de datos como pendientes de aceptacion.
	"""

	cursor = connection.cursor()

	if request.method == 'GET':
		sql = "SELECT nombre FROM test.departamento"
		cursor.execute(sql)
		departamentos = cursor.fetchall()

		return render_template("entidad_sanitaria_registro.html", departamentos=departamentos)
	else:
		tipo_id = request.form['tipo_id']
		num_id = request.form['num_id']
		nombre = request.form['nombre']
		
		municipio = request.form['municipio']
		barrio = request.form['barrio']
		sql = "SELECT id_barrio FROM test.barrio WHERE(nombre = '{}' AND municipio = '{}')".format(barrio,municipio)
		cursor.execute(sql)
		id_barrio = cursor.fetchall()[0][0]

		correo = request.form['correo']
		telefono = request.form['telefono']
		
		usuario = request.form['usuario']
		contrasena = (bcrypt.generate_password_hash(request.form['contrasena'].encode('utf-8'))).decode('utf-8')
		
		sql = "INSERT INTO test.entidad_sanitaria VALUES('{}',{},'{}','{}','{}',{},'{}',{},{})".format(tipo_id,num_id,usuario,contrasena,nombre,id_barrio,correo,telefono,1)
		cursor.execute(sql)
		connection.commit()
		
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
	cursor = connection.cursor()
	sql = "SELECT nombre FROM test.municipio WHERE(departamento = '{}')".format(dep)
	cursor.execute(sql)
	aux = cursor.fetchall()
	municipios = list()
	for m in aux: municipios.append(m[0])
	return jsonify({'municipios':municipios})


@app.route("/barrios/<mun>")
def obtener_barrios(mun):
	"""
	Recibe el nombre de un municipio y retorna
	una pagina en formato Json con los barrios
	correspondientes.
	"""
	cursor = connection.cursor()
	sql = "SELECT nombre FROM test.barrio WHERE(municipio = '{}')".format(mun)
	cursor.execute(sql)
	aux = cursor.fetchall()
	barrios = list()
	for m in aux: barrios.append(m[0])
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
	cursor = connection.cursor()
	num_id = int(num_id)
	sql = "SELECT tipo_id FROM test.{} WHERE(tipo_id = '{}' AND num_id = {})".format(tipo_tabla,tipo_id,num_id)
	cursor.execute(sql)
	aux = cursor.fetchall()
	docs = list()
	for d in aux: docs.append(d[0])
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
	cursor = connection.cursor()
	sql1 = "SELECT usuario FROM test.civil WHERE('{}' = usuario)".format(usr)
	sql2 = "SELECT usuario FROM test.administrador WHERE('{}' = usuario)".format(usr)
	sql3 = "SELECT usuario FROM test.comercio WHERE('{}' = usuario)".format(usr)
	sql4 = "SELECT usuario FROM test.entidad_sanitaria WHERE('{}' = usuario)".format(usr)
	cursor.execute(sql1)
	user1 = cursor.fetchall()
	cursor.execute(sql2)
	user2 = cursor.fetchall()
	cursor.execute(sql3)
	user3 = cursor.fetchall()
	cursor.execute(sql4)
	user4 = cursor.fetchall()

	usuarios = list()
	for u1 in user1: usuarios.append(u1[0])
	for u2 in user2: usuarios.append(u2[0])
	for u3 in user3: usuarios.append(u3[0])
	for u4 in user4: usuarios.append(u4[0])

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
		cursor = connection.cursor()

		#Decodificar imagen QR
		aux1 = decode(Image.open(request.files['codigo_QR']))
		#Leer informacion del codigo QR
		aux = aux1[0].data.decode('ascii')
		tipo_id, num_id = aux[:2],aux[3:]
		sql = "SELECT COUNT(*) FROM test.civil WHERE(tipo_id = '{}' AND num_id = {})".format(tipo_id,num_id)
		cursor.execute(sql)
		usuario = cursor.fetchone()
		if not usuario[0]:
			flash('no_usuario')
			return render_template("local_QR.html")
		
		sql = "SELECT fecha,resultado FROM test.historial_pruebas WHERE(tipo_id_persona = '{}' AND num_id_persona = {}) ORDER BY fecha DESC".format(tipo_id,num_id)
		cursor.execute(sql)
		prueba = cursor.fetchall()

		permitido = 1
		if len(prueba):
			#Si no se ha hecho una prueba de COVID-19 en los ultimos 15 dias, debe estar en cuarentena
			fecha = prueba[0][0]
			fecha = date(int(fecha[:4]),int(fecha[5:7]),int(fecha[8:]))
			fechaMin = date.today() - timedelta(days=15)
			if prueba[0][1]!='Negativo' and fecha >= fechaMin: permitido = 0

		tapabocas = 'SI'
		if 'tapabocas' not in request.form:
			permitido = 0
			tapabocas = 'NO'

		if not 35<=float(request.form['temp'])<38: permitido = 0

		if permitido: ingreso = 'SI'
		else: ingreso = 'NO'

		sql = "SELECT COUNT(*) FROM test.visita"
		cursor.execute(sql)
		N = cursor.fetchone()[0]

		fechayhora = datetime.fromtimestamp(time()).strftime('%Y-%m-%d %H:%M:%S')
		sql = "INSERT INTO test.visita VALUES({},'{}',{},'{}','{}',{},'{}',{},'{}')".format(N+1,tipo_id,num_id,fechayhora,session['tipo_id'],session['num_id'],tapabocas,request.form['temp'],ingreso)
		cursor.execute(sql)
		connection.commit()

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
		cursor = connection.cursor()

		tipo_id, num_id = request.form['tipo_id'], request.form['num_id']
		sql = "SELECT COUNT(*) FROM test.civil WHERE(tipo_id = '{}' AND num_id = {})".format(tipo_id,num_id)
		cursor.execute(sql)
		usuario = cursor.fetchone()
		if not usuario[0]:
			flash('no_usuario')
			return render_template("local_no_QR.html")

		sql = "SELECT fecha,resultado FROM test.historial_pruebas WHERE(tipo_id_persona = '{}' AND num_id_persona = {}) ORDER BY fecha DESC".format(tipo_id,num_id)
		cursor.execute(sql)
		prueba = cursor.fetchall()

		permitido = 1
		if len(prueba):
			#Si no se ha hecho una prueba de COVID-19 en los ultimos 15 dias, debe estar en cuarentena
			fecha = prueba[0][0]
			fecha = date(int(fecha[:4]),int(fecha[5:7]),int(fecha[8:]))
			fechaMin = date.today() - timedelta(days=15)
			if prueba[0][1]!='Negativo' and fecha >= fechaMin: permitido = 0

		tapabocas = 'SI'
		if 'tapabocas' not in request.form:
			permitido = 0
			tapabocas = 'NO'

		if not 35<=float(request.form['temp'])<38: permitido = 0

		if permitido: ingreso = 'SI'
		else: ingreso = 'NO'

		sql = "SELECT COUNT(*) FROM test.visita"
		cursor.execute(sql)
		N = cursor.fetchone()[0]

		fechayhora = datetime.fromtimestamp(time()).strftime('%Y-%m-%d %H:%M:%S')
		sql = "INSERT INTO test.visita VALUES({},'{}',{},'{}','{}',{},'{}',{},'{}')".format(N+1,tipo_id,num_id,fechayhora,session['tipo_id'],session['num_id'],tapabocas,request.form['temp'],ingreso)
		cursor.execute(sql)
		connection.commit()

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
		cursor = connection.cursor()

		tipo_id, num_id = request.form['tipo_id'], request.form['num_id']
		sql = "SELECT COUNT(*) FROM test.civil WHERE(tipo_id = '{}' AND num_id = {})".format(tipo_id,num_id)
		cursor.execute(sql)
		usuario = cursor.fetchone()
		if not usuario[0]:
			flash('no_usuario')
			return render_template("local_no_QR_des.html")

		sql = "SELECT fecha FROM test.historial_pruebas WHERE(tipo_id_persona = '{}' AND num_id_persona = {}) ORDER BY fecha DESC".format(tipo_id,num_id)
		cursor.execute(sql)
		prueba = cursor.fetchall()

		fechayhora = request.form['fecha']+' '+request.form['hora']+':00'

		tapabocas = 'SI'
		if 'tapabocas' not in request.form: tapabocas = 'NO'

		if not 35<=float(request.form['temp'])<38: permitido = 0

		sql = "SELECT COUNT(*) FROM test.visita"
		cursor.execute(sql)
		N = cursor.fetchone()[0]

		fechayhora = datetime.fromtimestamp(time()).strftime('%Y-%m-%d %H:%M:%S')
		sql = "INSERT INTO test.visita VALUES({},'{}',{},'{}','{}',{},'{}',{},'{}')".format(N+1,tipo_id,num_id,fechayhora,session['tipo_id'],session['num_id'],tapabocas,request.form['temp'],'SI')
		cursor.execute(sql)
		connection.commit()

		return redirect(url_for("index"))


@app.route("/registro-prueba/",methods=["POST"])
def registro_prueba():
	if 'tipo' in session and session['tipo'] == 3:
		cursor = connection.cursor()

		tipo_id, num_id = request.form['tipo_id1'], request.form['num_id1']
		sql = "SELECT COUNT(*) FROM test.civil WHERE(tipo_id = '{}' AND num_id = {})".format(tipo_id,num_id)
		cursor.execute(sql)
		usuario = cursor.fetchone()
		if not usuario[0]:
			flash('no_usuario')
			return redirect(url_for("index"))

		sql = "SELECT id_historial FROM test.historial_pruebas WHERE(id_historial = {} AND tipo_id_entidad = '{}' AND num_id_entidad = {})".format(request.form['prueba_id1'],session['tipo_id'],session['num_id'])
		N = cursor.execute(sql)
		if N:
			flash('no_historial')
			return redirect(url_for("index"))

		sql = "SELECT fechayhora,resultado FROM test.historial_pruebas WHERE(tipo_id_persona = '{}' AND num_id_persona = {} AND tipo_id_entidad = '{}' AND num_id_entidad = {}) ORDER BY fechayhora DESC".format(tipo_id,num_id,session['tipo_id'],session['num_id'])
		cursor.execute(sql)
		prueba = cursor.fetchall()

		if len(prueba) and prueba[0][1] == "Ninguno":
			flash('pendiente')
			return redirect(url_for("index"))

		fechayhora = datetime.fromtimestamp(time()).strftime('%Y-%m-%d %H:%M:%S')
		sql = "INSERT INTO test.historial_pruebas VALUES({},'{}',{},'{}',{},'{}','Ninguno')".format(request.form['prueba_id1'],request.form['tipo_id1'],request.form['num_id1'],session['tipo_id'],session['num_id'],fechayhora)
		cursor.execute(sql)
		connection.commit()

		return redirect(url_for("index"))


@app.route("/registro-resultado/",methods=["POST"])
def registro_resultado():
	if 'tipo' in session and session['tipo'] == 3:
		cursor = connection.cursor()

		sql = "SELECT resultado FROM test.historial_pruebas WHERE(id_historial = {} AND tipo_id_entidad = '{}' AND num_id_entidad = {})".format(request.form['prueba_id2'],session['tipo_id'],session['num_id'])
		N = cursor.execute(sql)
		resultado = cursor.fetchone()
		if not N:
			flash('no_prueba')
			return redirect(url_for("index"))

		if resultado[0] != "Ninguno":
			flash('reportado')
			return redirect(url_for("index"))

		sql = "UPDATE test.historial_pruebas SET resultado = '{}' WHERE (id_historial = {} AND tipo_id_entidad = '{}' AND num_id_entidad = '{}')".format(request.form['desicion'],request.form['prueba_id2'],session['tipo_id'],session['num_id'])
		cursor.execute(sql)
		connection.commit()
		
		return redirect(url_for("index"))


@app.route("/gestionar-locales/")
def gestionar_locales():
	return render_template("admin_gestionarLocales.html")


@app.route("/gestionar-solicitudes/")
def gestionar_solicitudes():
	return render_template("admin_gestionarSolicitudes.html")


@app.route("/gestionar-usuarios/")
def gestionar_usuarios():
	return render_template("admin_gestionarUsuarios.html")


@app.route("/gestionar-admins/")
def gestionar_admins():
	return render_template("admin_gestionarAdmins.html")


@app.route("/gestionar-barrios/")
def gestionar_barrios():
	return render_template("admin_gestionarBarrios.html")


@app.route("/gestionar-categorias/")
def gestionar_categorias():
	return render_template("admin_gestionarCategorias.html")


if __name__ == "__main__":
	app.secret_key = "jda()/_s8U9??¡!823jeD"
	app.run(debug=True)	