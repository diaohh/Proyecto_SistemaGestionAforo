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
contrasena2.onkeyup = function(){ comparar_contrasenas() }
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


var departamento = document.getElementById("departamento");
var municipio = document.getElementById("municipio");
var mun = document.getElementById("mun_seleccionado").value;
function actualizarMuns(){
	dep = departamento.value;
	fetch('/muns/'+dep).then(function(aux){
		aux.json().then(function(muns){
			let auxHTML = '';
			for(let m of muns.municipios){
				if(m == mun){
					auxHTML += '<option value="'+ m +'" selected>'+ m +'</option>';
				}else{
					auxHTML += '<option value="'+ m +'">'+ m +'</option>';
				}
			}
			municipio.innerHTML = auxHTML;
		})
	});
}
departamento.onchange = function(){ actualizarMuns(); }


var barrio = document.getElementById("barrio");
var bar = document.getElementById("barrio_seleccionado").value;
function actualizarBarrios(){
	mun = municipio.value;
	fetch('/barrios/'+mun).then(function(aux){
		aux.json().then(function(bars){
			let auxHTML = '';
			for(let b of bars.barrios){
				if(b == bar){
					auxHTML += '<option value="'+ b +'" selected>'+ b +'</option>';
				}else{
					auxHTML += '<option value="'+ b +'">'+ b +'</option>';
				}
			}
			barrio.innerHTML = auxHTML;
		})
	});
}
municipio.onchange = function(){ actualizarBarrios(); }