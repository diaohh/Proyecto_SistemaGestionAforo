from flask import Flask, render_template, redirect, url_for, request, jsonify, flash, session
from flask_bcrypt import Bcrypt
import pymysql

app = Flask(__name__)
bcrypt = Bcrypt(app)
connection = pymysql.connect(
		host='localhost', #ip
		user='root',
		password='',
		db=''
	)


@app.route("/")
def index():
	if "tipo" in session:
		if session["tipo"] == 1:
			return render_template("usuario.html")
		if session["tipo"] == 2:
			return render_template("local.html")
		if session["tipo"] == 3:
			return render_template("entidad_sanitaria.html")
		if session["tipo"] == 4:
			return render_template("admin.html")
	else:
		return render_template("index.html")


@app.route("/objetivo")
def objetivo():
	return render_template("objetivo.html")


@app.route("/contactanos")
def contactanos():
	return render_template("contactanos.html")


@app.route("/inicio-sesion/",methods=["GET","POST"])
def inicio_sesion():
	
	cursor = connection.cursor()
	
	if request.method =='GET':
		return render_template("inicio_de_sesion.html")
	else: 
		usuario = request.form['usuario']
		contrasena = request.form['contrasena']
		tipo_cuenta = 0 # 1: Civil, 2: Comercio, 3: Entidad Sanitaria, 4: admin

		sql1 = "SELECT usuario,contrasena,pendiente FROM test.civil WHERE('{}' = usuario)".format(usuario)
		sql2 = "SELECT usuario,contrasena,pendiente FROM test.comercio WHERE('{}' = usuario)".format(usuario)
		sql3 = "SELECT usuario,contrasena,pendiente FROM test.entidad_sanitaria WHERE('{}' = usuario)".format(usuario)
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
	session.clear()
	return redirect(url_for("index"))

@app.route("/registro-usuario/",methods=["GET","POST"])
def registro_usuario():
	
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
	cursor = connection.cursor()
	sql = "SELECT nombre FROM test.municipio WHERE(departamento = '{}')".format(dep)
	cursor.execute(sql)
	aux = cursor.fetchall()
	municipios = list()
	for m in aux: municipios.append(m[0])
	return jsonify({'municipios':municipios})


@app.route("/barrios/<mun>")
def obtener_barrios(mun):
	cursor = connection.cursor()
	sql = "SELECT nombre FROM test.barrio WHERE(municipio = '{}')".format(mun)
	cursor.execute(sql)
	aux = cursor.fetchall()
	barrios = list()
	for m in aux: barrios.append(m[0])
	return jsonify({'barrios':barrios})


@app.route("/id/<tipo_tabla>/<tipo_id>/<num_id>")
def obtener_documentos(tipo_tabla,tipo_id,num_id):
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


if __name__ == "__main__":
	app.secret_key = "jda()/_s8U9??¡!823jeD"
	app.run(debug=True)	