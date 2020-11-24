var contrasena = document.getElementById("contrasena");
var contrasena2 = document.getElementById("contrasena2");
var numero = document.getElementById("numero");
var letra = document.getElementById("letra");
var caracter = document.getElementById("caracter");
var longitud = document.getElementById("longitud");
var boton = document.getElementById("terminar");
var contrasena2_l = document.getElementById("contrasena2_l");
var esvalido_contrasena = false;
var esvalido_contrasena2 = false;
var esvalido_documento = false;
var esvalido_usuario = false;

var tmp1 = window.location.href.split('/');
var url = tmp1[tmp1.length-2];
var tipo_usuario = '';
if(!(url.localeCompare('registro-local'))){ tipo_usuario = 'comercio'; }
else if(!(url.localeCompare('registro-usuario'))){ tipo_usuario = 'civil'; }
else{ tipo_usuario = 'entidad_sanitaria'; }

contrasena.onkeyup = function() {

	var nums = contrasena.value.match(/[0-9]/g); 
	if(nums){
		numero.innerHTML = "- <span>&#10003;</span>";
	}else{
		numero.innerHTML = "";
	}

	var letras = contrasena.value.match(/[A-Z]|[a-z]/g);
	if(letras){
		letra.innerHTML = "- <span>&#10003;</span>";
	}else{
		letra.innerHTML = "";
	}

	simbolos = contrasena.value.match(/[-_!=+?¿!¡]/g)
	if(simbolos){
		caracter.innerHTML = "- <span>&#10003;</span>";
	}else{
		caracter.innerHTML = "";
	}

	largo = contrasena.value.length > 9;
	if(largo){
		longitud.innerHTML = "- <span>&#10003;</span>";
	}else{
		longitud.innerHTML = "";
	}

	if(nums && letras && simbolos && largo){
		esvalido_contrasena = true;
	}else{
		esvalido_contrasena = false;
	}

	comparar_contrasenas()
}
contrasena2.onblur = function(){ comparar_contrasenas() }
function comparar_contrasenas(){
	var aux1 = contrasena.value;
	var aux2 = contrasena2.value
	var aux3 = aux2.localeCompare(aux1)
	if(aux3 != 0){ contrasena2_l.innerHTML = "las contraseñas no coinciden"; }
	else{ contrasena2_l.innerHTML = ""; }

	esvalido_contrasena2 = !(aux3)
	if(esvalido_contrasena && esvalido_contrasena2 && esvalido_usuario){
		boton.disabled = false;
	}else{
		boton.disabled = true;
	}
}

var label_num_doc = document.getElementById("label_num_doc");
var tipo_id = document.getElementById("tipo_id");
var num_id = document.getElementById("num_id");
num_id.onblur = function(){
	num = num_id.value;
	tip = tipo_id.value;
	if(num.length && num.match(/[0-9]/g)){
		fetch('/id/'+tipo_usuario+'/'+tip+'/'+num).then(function(aux){
			aux.json().then(function(doc){
				if(doc.docs.length == 0){
					esvalido_documento = true;
					label_num_doc.innerHTML = "";
				}else{
					esvalido_documento = false;
					label_num_doc.innerHTML = "Tipo y numero de documento ya existentes";
				}
			})
		});
	}else{ esvalido_documento = false; }
}

var departamento = document.getElementById("departamento")
var municipio = document.getElementById("municipio")
function actualizarMuns(){
	dep = departamento.value;
	fetch('/muns/'+dep).then(function(aux){
		aux.json().then(function(muns){
			let auxHTML = '';
			for(let m of muns.municipios){
				auxHTML += '<option value="'+ m +'">'+ m +'</option>';
			}
			municipio.innerHTML = auxHTML;
		})
	});
}
departamento.onchange = function(){ actualizarMuns(); }

var barrio = document.getElementById("barrio")
function actualizarBarrios(){
	mun = municipio.value;
	fetch('/barrios/'+mun).then(function(aux){
		aux.json().then(function(bars){
			let auxHTML = '';
			for(let b of bars.barrios){
				auxHTML += '<option value="'+ b +'">'+ b +'</option>';
			}
			barrio.innerHTML = auxHTML;
		})
	});
}
municipio.onchange = function(){ actualizarBarrios(); }

var label_usuario = document.getElementById("label_usuario");
var usuario = document.getElementById("usuario");
usuario.onblur = function(){
	usr = usuario.value;
	if(usr.length){
		fetch('/user/'+usr).then(function(aux){
			aux.json().then(function(usrs){
				if(usrs.usuarios.length == 0){
					esvalido_usuario = true;
					label_usuario.innerHTML = "";
				}else{
					esvalido_usuario = false;
					label_usuario.innerHTML = "Usuario ya existente";
				}
			})
		});
	}else{ esvalido_usuario = false; }

	if(esvalido_contrasena && esvalido_contrasena2 && esvalido_usuario){
		boton.disabled = false;
	}else{
		boton.disabled = true;
	}

}