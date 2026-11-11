"""Puerta de enlace de API y tablero web."""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PAGINA = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#161616">
<title>Plataforma Urbana Integrada · Operación</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600&display=swap">
<style>
:root{color-scheme:dark;--fondo:#161616;--tarjeta:#0d0d0d;--regla:#2e2e2e;--texto:#f4f4f4;--tenue:#a8a8a8;
--acento:#4589ff;--bien:#42be65;--aviso:#f1c21b;--mal:#fa4d56;--barra:#525252}
*{box-sizing:border-box}
html{background:var(--fondo)}
body{margin:0;font:14px/1.45 "IBM Plex Sans","Helvetica Neue",Arial,sans-serif;color:var(--texto);
font-variant-numeric:tabular-nums;-webkit-tap-highlight-color:transparent;touch-action:manipulation}
a{color:inherit;text-decoration:none}
a:focus-visible{outline:2px solid var(--acento);outline-offset:3px}
.salto{position:absolute;left:-999px}.salto:focus{left:16px;top:8px;background:var(--tarjeta);padding:8px 12px;z-index:2}
.marco{max-width:1320px;margin:0 auto;padding:0 32px}
header .marco{display:flex;align-items:center;gap:12px;height:56px}
.marca{width:22px;height:22px;flex:none}
h1{font-size:16px;font-weight:600;margin:0;text-wrap:balance}
.ambito{color:var(--tenue);margin-left:auto;text-align:right}
nav{border-top:1px solid var(--regla);border-bottom:1px solid var(--regla)}
nav .marco{display:flex;gap:28px;overflow-x:auto}
nav a{padding:12px 0 11px;color:var(--tenue);border-bottom:1px solid transparent;margin-bottom:-1px;white-space:nowrap}
nav a:hover{color:var(--texto)}
nav a[aria-current="page"]{color:var(--texto);border-bottom-color:var(--acento)}
main{padding:28px 0 48px}
.cifras{display:grid;grid-template-columns:repeat(4,1fr);gap:24px;margin:0 0 28px;padding:0}
.cifras div{min-width:0}
.cifras dt{color:var(--tenue);font-size:13px}
.cifras dd{margin:2px 0 0;font-size:32px;line-height:1.2;font-weight:600;letter-spacing:-.01em}
.cifras small{display:block;font-size:13px;font-weight:400;color:var(--tenue);letter-spacing:0}
.fila{display:grid;grid-template-columns:5fr 7fr;gap:24px;margin-bottom:24px}
section{background:var(--tarjeta);padding:20px 24px 22px;min-width:0}
h2{font-size:14px;font-weight:600;margin:0 0 4px}
.nota{color:var(--tenue);margin:0 0 16px;font-size:13px}
.embudo{display:grid;grid-template-columns:auto 1fr auto;gap:8px 12px;align-items:center;margin-bottom:20px}
.pista{height:10px;background:#1f1f1f}
.pista i{display:block;height:10px;background:var(--barra);transform-origin:left;transition:transform .4s ease-out}
.pista i.dato{background:var(--acento)}
.num{text-align:right}
table{width:100%;border-collapse:collapse}
th{font-weight:400;color:var(--tenue);text-align:left;font-size:13px;padding:0 0 8px}
td{padding:9px 12px 9px 0;border-top:1px solid var(--regla)}
th{padding-right:12px}
td:last-child,th:last-child{padding-right:0}
th.num,td.num{text-align:right;padding-left:16px}
.estado::before{content:"";display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:8px;background:var(--bien)}
.estado.sin::before{background:var(--mal)}
.cont{display:grid;grid-template-columns:92px 1fr 52px;gap:10px 14px;align-items:center}
.cont .pista{position:relative;height:14px}
.cont .pista i{height:14px}
.cont .pista::after{content:"";position:absolute;left:80%;top:-3px;bottom:-3px;width:1px;background:var(--texto)}
.cont .lleno{background:var(--mal)}
.cont .detalle{grid-column:2/4;color:var(--tenue);font-size:12px;margin-top:-8px}
.leyenda{color:var(--tenue);font-size:12px;margin:14px 0 0}
ul{list-style:none;margin:0;padding:0}
li{padding:9px 0;border-top:1px solid var(--regla);display:flex;gap:16px;overflow-wrap:anywhere}
li span:first-child{color:var(--tenue);flex:none;width:64px}
.vacio{color:var(--tenue);padding:10px 0;border-top:1px solid var(--regla)}
#aviso{color:var(--aviso);margin:0 0 20px}
#aviso:empty{display:none}
@media (max-width:860px){.marco{padding:0 16px}.cifras{grid-template-columns:1fr 1fr}.fila{grid-template-columns:1fr}
.cifras dd{font-size:26px}.ambito{display:none}section{padding:16px}}
@media (prefers-reduced-motion:reduce){.pista i{transition:none}}
</style>
</head>
<body>
<a class="salto" href="#contenido">Saltar al contenido</a>
<header><div class="marco">
<svg class="marca" viewBox="0 0 22 22" aria-hidden="true"><path d="M3 19V9l5-4v14M9.5 19V3l6 3v13M17 19v-8l2.5 1.5V19" fill="none" stroke="#4589ff" stroke-width="1.6"/></svg>
<h1 translate="no">Plataforma Urbana Integrada</h1>
<span class="ambito" id="ambito">Operación de la ciudad</span>
</div></header>
<nav aria-label="Dominio"><div class="marco" id="pestanas">
<a href="?dominio=todos" data-d="todos">Todos</a>
<a href="?dominio=energia" data-d="energia">Energía</a>
<a href="?dominio=movilidad" data-d="movilidad">Movilidad</a>
<a href="?dominio=residuos" data-d="residuos">Residuos</a>
</div></nav>
<main id="contenido"><div class="marco">
<p id="aviso" role="status" aria-live="polite"></p>
<dl class="cifras">
<div><dt>Lecturas recibidas en el borde</dt><dd id="k-rec">0</dd></div>
<div><dt>Mensajes enviados a la nube</dt><dd id="k-env">0</dd></div>
<div><dt>Tráfico evitado</dt><dd id="k-red">0&nbsp;%</dd></div>
<div><dt>Contenedores por recoger</dt><dd id="k-cont">0</dd></div>
</dl>
<div class="fila">
<section aria-labelledby="t-borde"><h2 id="t-borde">Filtrado en el borde</h2>
<p class="nota">De cada lectura de los sensores, cuántas llegan a la nube.</p>
<div class="embudo" id="embudo"></div>
<table><thead><tr><th>Pasarela</th><th>Enlace</th><th class="num">Recibidas</th><th class="num">Enviadas</th><th class="num">En búfer</th></tr></thead>
<tbody id="pasarelas"></tbody></table></section>
<section aria-labelledby="t-cont"><h2 id="t-cont">Llenado de contenedores</h2>
<p class="nota">Último promedio por contenedor. La línea marca el 80&nbsp;%, umbral de recolección.</p>
<div class="cont" id="contenedores"></div></section>
</div>
<div class="fila">
<section aria-labelledby="t-alertas"><h2 id="t-alertas">Alertas de recolección</h2>
<p class="nota">Las diez más recientes.</p>
<ul id="alertas" aria-live="polite"></ul></section>
<section aria-labelledby="t-prom"><h2 id="t-prom">Promedios por dominio y zona</h2>
<p class="nota" id="n-prom">Energía en kWh por luminaria, movilidad en vehículos por minuto, residuos en % de llenado.</p>
<table><thead><tr><th>Dominio</th><th>Zona</th><th class="num">Promedio</th><th class="num">Pronóstico</th><th class="num">Registros</th></tr></thead>
<tbody id="promedios"></tbody></table></section>
</div>
</div></main>
<script>
const NOMBRE={energia:"Energía",movilidad:"Movilidad",residuos:"Residuos"};
const UNIDAD={energia:" kWh",movilidad:" veh/min",residuos:" %"};
const entero=new Intl.NumberFormat("es-CO");
const decimal=new Intl.NumberFormat("es-CO",{maximumFractionDigits:2});
const hora=new Intl.DateTimeFormat("es-CO",{hour:"2-digit",minute:"2-digit",second:"2-digit"});
const $=id=>document.getElementById(id);
const el=(tag,cls,txt)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(txt!==undefined)e.textContent=txt;return e;};
let dominio=new URLSearchParams(location.search).get("dominio")||"todos";
if(dominio!=="todos"&&!NOMBRE[dominio])dominio="todos";
let datos=null;

function marcar(){for(const a of $("pestanas").children){if(a.dataset.d===dominio)a.setAttribute("aria-current","page");else a.removeAttribute("aria-current");}}
$("pestanas").addEventListener("click",e=>{const a=e.target.closest("a");if(!a||e.metaKey||e.ctrlKey||e.shiftKey)return;
  e.preventDefault();dominio=a.dataset.d;history.pushState(null,"",a.getAttribute("href"));marcar();pintar();});
addEventListener("popstate",()=>{dominio=new URLSearchParams(location.search).get("dominio")||"todos";marcar();pintar();});

function vacio(nodo,texto,columnas){nodo.replaceChildren();
  if(columnas){const tr=el("tr"),td=el("td","vacio",texto);td.colSpan=columnas;tr.append(td);nodo.append(tr);}
  else nodo.append(el("div","vacio",texto));}

function pintar(){if(!datos)return;const b=datos.borde;
  $("k-rec").replaceChildren(entero.format(b.recibidas),el("small","",entero.format(b.descartadas)+" descartadas por inválidas"));
  $("k-env").textContent=entero.format(b.enviadas);
  $("k-red").textContent=decimal.format(b.reduccion)+" %";
  const llenos=datos.contenedores.filter(c=>c[2]>=80).length;
  $("k-cont").replaceChildren(String(llenos),el("small","","de "+datos.contenedores.length+" con medición"));
  $("ambito").textContent=datos.pasarelas.length+" zonas · actualizado "+hora.format(new Date());

  const e=$("embudo");e.replaceChildren();
  for(const [nombre,valor,cls] of [["Borde",b.recibidas,""],["Nube",b.enviadas,"dato"]]){
    const pista=el("div","pista"),i=el("i",cls);i.style.transform="scaleX("+(b.recibidas?valor/b.recibidas:0)+")";pista.append(i);
    e.append(el("span","",nombre),pista,el("span","num",entero.format(valor)));}

  const p=$("pasarelas");p.replaceChildren();
  for(const g of datos.pasarelas){const tr=el("tr");
    tr.append(el("td","",g.zona),el("td","estado"+(g.enlace?"":" sin"),g.enlace?"Activo":"Sin enlace"),
      el("td","num",entero.format(g.recibidas)),el("td","num",entero.format(g.enviadas)),el("td","num",entero.format(g.en_bufer)));p.append(tr);}

  const c=$("contenedores");
  if(!datos.contenedores.length)vacio(c,"Aún no hay mediciones de contenedores.");
  else{c.replaceChildren();for(const [sensor,zona,valor,detalle] of datos.contenedores){
    const pista=el("div","pista"),i=el("i",valor>=80?"lleno":"dato");i.style.transform="scaleX("+Math.min(valor,100)/100+")";pista.append(i);
    c.append(el("span","",sensor),pista,el("span","num",decimal.format(valor)+" %"),el("span","detalle",zona+" · "+(detalle||"sin pronóstico")));}}

  const a=$("alertas");
  if(!datos.alertas.length)vacio(a,"Sin alertas. Ningún contenedor ha superado el 80 %.");
  else{a.replaceChildren();for(const [zona,mensaje] of datos.alertas){const li=el("li");li.append(el("span","",zona),el("span","",mensaje));a.append(li);}}

  const t=$("promedios"),filas=datos.promedios.filter(f=>dominio==="todos"||f[0]===dominio);
  if(!filas.length)vacio(t,"Aún no hay registros de "+(NOMBRE[dominio]||"ningún dominio").toLowerCase()+".",5);
  else{t.replaceChildren();for(const [d,zona,promedio,registros,pronostico] of filas){const tr=el("tr");
    tr.append(el("td","",NOMBRE[d]),el("td","",zona),el("td","num",decimal.format(promedio)+UNIDAD[d]),
      el("td","num",pronostico==null?"–":decimal.format(pronostico)+UNIDAD[d]),el("td","num",entero.format(registros)));t.append(tr);}}
}

async function cargar(){try{const r=await fetch("/api/resumen");if(!r.ok)throw new Error(r.status);
    datos=await r.json();$("aviso").textContent="";pintar();}
  catch(err){$("aviso").textContent="Sin conexión con la plataforma. La simulación terminó o el servidor se detuvo. Ejecute de nuevo python main.py.";}}
marcar();cargar();setInterval(cargar,2000);
</script>
</body>
</html>"""


def resumen(almacen, pasarelas):
    recibidas = sum(p.recibidas for p in pasarelas)
    enviadas = sum(p.enviadas for p in pasarelas)
    return {
        "borde": {"recibidas": recibidas, "enviadas": enviadas,
                  "descartadas": sum(p.descartadas for p in pasarelas),
                  "en_bufer": sum(p.en_bufer for p in pasarelas),
                  "reduccion": round(100 * (1 - enviadas / recibidas), 1) if recibidas else 0.0},
        "pasarelas": [{"zona": p.zona, "enlace": p.enlace_activo, "recibidas": p.recibidas,
                       "enviadas": p.enviadas, "en_bufer": p.en_bufer} for p in pasarelas],
        # dominio, zona, promedio, registros, pronóstico medio de los sensores de esa zona
        "promedios": almacen.ejecutar(
            """SELECT m.dominio, m.zona, ROUND(AVG(m.valor), 3), COUNT(*),
                      (SELECT ROUND(AVG(p.valor), 3) FROM pronosticos p
                        WHERE p.dominio = m.dominio AND p.sensor IN
                              (SELECT sensor FROM mediciones x WHERE x.dominio = m.dominio AND x.zona = m.zona))
               FROM mediciones m GROUP BY m.dominio, m.zona ORDER BY 1, 2"""),
        # sensor, zona, último promedio, detalle del pronóstico
        "contenedores": almacen.ejecutar(
            """SELECT m.sensor, m.zona, m.valor, p.detalle FROM mediciones m
               LEFT JOIN pronosticos p ON p.sensor = m.sensor
               WHERE m.dominio = 'residuos' AND m.id IN (SELECT MAX(id) FROM mediciones GROUP BY sensor)
               ORDER BY m.valor DESC"""),
        "pronosticos": almacen.ejecutar("SELECT sensor, dominio, valor, detalle FROM pronosticos ORDER BY 2, 1"),
        "alertas": almacen.ejecutar("SELECT zona, mensaje FROM alertas ORDER BY id DESC LIMIT 10"),
    }


def iniciar_api(almacen, pasarelas, puerto=8000):
    class Manejador(BaseHTTPRequestHandler):
        def do_GET(self):
            ruta = self.path.split("?")[0]
            if ruta == "/api/resumen":
                cuerpo, tipo = json.dumps(resumen(almacen, pasarelas), ensure_ascii=False).encode(), "application/json"
            elif ruta == "/":
                cuerpo, tipo = PAGINA.encode(), "text/html"
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", tipo + "; charset=utf-8")
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)

        def log_message(self, *args):    # sin ruido en la consola
            pass

    servidor = ThreadingHTTPServer(("127.0.0.1", puerto), Manejador)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    return servidor
