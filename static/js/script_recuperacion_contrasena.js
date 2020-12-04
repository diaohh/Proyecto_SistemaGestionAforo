seleccion1 = document.getElementById("usuario_sel");
seleccion2 = document.getElementById("local_sel");
seleccion3 = document.getElementById("entidad_sanitaria_sel");
form_usuario = document.getElementById("form_usuario");
form_local = document.getElementById("form_local");
form_entidad_sanitaria = document.getElementById("form_entidad_sanitaria");

seleccion1.onclick = function() {
	form_usuario.style.display = "inline";
	form_local.style.display = "none";
	form_entidad_sanitaria.style.display = "none";
}
seleccion2.onclick = function() {
	form_usuario.style.display = "none";
	form_local.style.display = "inline";
	form_entidad_sanitaria.style.display = "none";
}
seleccion3.onclick = function() {
	form_usuario.style.display = "none";
	form_local.style.display = "none";
	form_entidad_sanitaria.style.display = "inline";
}

function actualizar_telefonos(selection){		
	if(selection=='1'){
		document.formulario_local.telefono2.disabled = true;
		document.formulario_local.telefono3.disabled = true;
		document.getElementById("telefono2").value = ''; 
		document.getElementById("telefono3").value = ''; 
	}
	else if(selection=='2'){
		document.formulario_local.telefono2.disabled = false;
		document.formulario_local.telefono3.disabled = true;
		document.getElementById("telefono3").value = ''; 
	}
	else if(selection=='3'){
		document.formulario_local.telefono2.disabled = false;
		document.formulario_local.telefono3.disabled = false;
	}
}


var departamento1 = document.getElementById("departamento1")
var municipio1 = document.getElementById("municipio1")
function actualizarMuns1(){
	dep = departamento1.value;
	fetch('/muns/'+dep).then(function(aux){
		aux.json().then(function(muns){
			muns.municipios.sort();
			let auxHTML = '';
			for(let m of muns.municipios){
				auxHTML += '<option value="'+ m +'">'+ m +'</option>';
			}
			municipio1.innerHTML = auxHTML;
		})
	});
}
departamento1.onchange = function(){ actualizarMuns1(); }

var barrio1 = document.getElementById("barrio1")
function actualizarBarrios1(){
	mun = municipio1.value;
	fetch('/barrios/'+mun).then(function(aux){
		aux.json().then(function(bars){
			bars.barrios.sort();
			let auxHTML = '';
			for(let b of bars.barrios){
				auxHTML += '<option value="'+ b +'">'+ b +'</option>';
			}
			barrio1.innerHTML = auxHTML;
		})
	});
}
municipio1.onchange = function(){ actualizarBarrios1(); }


var departamento2 = document.getElementById("departamento2")
var municipio2 = document.getElementById("municipio2")
function actualizarMuns2(){
	dep = departamento2.value;
	fetch('/muns/'+dep).then(function(aux){
		aux.json().then(function(muns){
			muns.municipios.sort();
			let auxHTML = '';
			for(let m of muns.municipios){
				auxHTML += '<option value="'+ m +'">'+ m +'</option>';
			}
			municipio2.innerHTML = auxHTML;
		})
	});
}
departamento2.onchange = function(){ actualizarMuns2(); }

var barrio2 = document.getElementById("barrio2")
function actualizarBarrios2(){
	mun = municipio2.value;
	fetch('/barrios/'+mun).then(function(aux){
		aux.json().then(function(bars){
			bars.barrios.sort();
			let auxHTML = '';
			for(let b of bars.barrios){
				auxHTML += '<option value="'+ b +'">'+ b +'</option>';
			}
			barrio2.innerHTML = auxHTML;
		})
	});
}
municipio2.onchange = function(){ actualizarBarrios2(); }


var departamento3 = document.getElementById("departamento3")
var municipio3 = document.getElementById("municipio3")
function actualizarMuns3(){
	dep = departamento3.value;
	fetch('/muns/'+dep).then(function(aux){
		aux.json().then(function(muns){
			muns.municipios.sort();
			let auxHTML = '';
			for(let m of muns.municipios){
				auxHTML += '<option value="'+ m +'">'+ m +'</option>';
			}
			municipio3.innerHTML = auxHTML;
		})
	});
}
departamento3.onchange = function(){ actualizarMuns3(); }

var barrio3 = document.getElementById("barrio3")
function actualizarBarrios3(){
	mun = municipio3.value;
	fetch('/barrios/'+mun).then(function(aux){
		aux.json().then(function(bars){
			bars.barrios.sort();
			let auxHTML = '';
			for(let b of bars.barrios){
				auxHTML += '<option value="'+ b +'">'+ b +'</option>';
			}
			barrio3.innerHTML = auxHTML;
		})
	});
}
municipio3.onchange = function(){ actualizarBarrios3(); }
