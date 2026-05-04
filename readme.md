# Prototipo del algoritmo de Dijkstra — Ruta UNAB → UIS

Implementación visual del algoritmo de Dijkstra para encontrar la ruta más corta entre la **Universidad Autónoma de Bucaramanga (UNAB)** y la **Universidad Industrial de Santander (UIS)** sobre la red vial real de Bucaramanga, respetando el sentido de las calles.

---

## Tabla de contenidos

1. [Objetivo](#1-objetivo)
2. [Fuente de datos geográficos](#2-fuente-de-datos-geográficos)
3. [Modelado como grafo](#3-modelado-como-grafo)
4. [Algoritmo de Dijkstra](#4-algoritmo-de-dijkstra)
5. [Implementación](#5-implementación)
6. [Resultados](#6-resultados)
7. [Cómo ejecutar](#7-cómo-ejecutar)
8. [Salidas que produce el programa](#8-salidas-que-produce-el-programa)
9. [Limitaciones y posibles mejoras](#9-limitaciones-y-posibles-mejoras)

---

## 1. Objetivo

Construir un prototipo en Python que calcule, sobre la malla vial real de Bucaramanga, la ruta más corta en distancia entre la UNAB (Campus El Jardín) y la UIS (Portería principal sobre Carrera 27), aplicando el algoritmo de Dijkstra con las siguientes consideraciones:

- Los **nodos del grafo son los cruces entre calles**.
- Las **aristas son los tramos de calle** entre cruces consecutivos, con peso igual a su longitud en metros.
- Se respetan los **sentidos viales** (one-ways) de Bucaramanga.

---

## 2. Fuente de datos geográficos

### 2.1 Fuente sugerida en el enunciado

El trabajo sugiere usar el visor del Geoportal de la Alcaldía de Bucaramanga:

> https://geodata.bucaramanga.gov.co/waportal/

Este visor publica oficialmente la malla vial del municipio. Sin embargo, presenta una limitación operativa: permite consultar la capa de forma interactiva pero **no expone una API ni un enlace de descarga vectorial directo** sobre el cual se pueda construir el grafo de manera automatizada. Tomar los datos de allí implicaría medir manualmente cada tramo y registrar cada sentido vial, lo cual no es viable a la escala del corredor UNAB–UIS.

### 2.2 Fuente utilizada

Se utiliza **OpenStreetMap (OSM)** a través de la librería **OSMnx** para Python. OSM es una base de datos cartográfica abierta y colaborativa que cubre Bucaramanga con la malla vial completa, incluyendo geometría de calles, longitudes y atributos de sentido (`oneway`). OSMnx descarga esa información y la entrega ya estructurada como un **grafo dirigido de NetworkX**, con cada arista etiquetada con su longitud real en metros.

> **Nota:** Esta decisión fue consultada con el docente y aprobada con la condición de documentar el procedimiento, lo cual se hace en este README y en el documento técnico anexo.

### 2.3 Validación

Se verificó por inspección visual que la red descargada de OSM coincide con la malla vial del Geoportal en el corredor UNAB–UIS, y que los sentidos de las vías principales (Carrera 27, Carrera 33, Calle 36, etc.) corresponden con los publicados oficialmente.

---

## 3. Modelado como grafo

El problema se modela como un grafo dirigido y ponderado **G = (V, E, w)** donde:

| Elemento       | Significado                                                               |
| -------------- | ------------------------------------------------------------------------- |
| `V` (vértices) | Cruces entre calles                                                       |
| `E` (aristas)  | Tramos de calle entre dos cruces consecutivos                             |
| `w(e)` (peso)  | Longitud en metros del tramo, calculada sobre la geometría real de la vía |

**Sentidos viales:** una calle de un solo sentido aparece como **una sola arista** en la dirección permitida; una de doble sentido se modela como **dos aristas**, una en cada dirección.

### 3.1 El "problema del último tramo" (snap a la red)

Las entradas de la UNAB y de la UIS **no son cruces de calles**, son puntos sobre tramos de vía. Como el grafo solo tiene nodos en intersecciones, cada coordenada se asocia al cruce más cercano (proceso conocido como _snap to network_) usando distancia haversine. Ese cruce se toma como nodo de partida o de llegada para Dijkstra.

En la visualización, los pocos metros entre la entrada real y el cruce snapeado se dibujan como **trazos punteados**, dejando claro qué parte del recorrido fue calculada por el algoritmo y qué parte corresponde al último tramo no modelado.

---

## 4. Algoritmo de Dijkstra

Dijkstra encuentra la ruta más corta entre un nodo origen y todos los demás cuando los pesos son no negativos —condición que se cumple aquí porque las distancias son siempre positivas.

### 4.1 Estrategia

1. Mantener una distancia tentativa para cada nodo (∞ inicialmente, salvo el origen que es 0).
2. Usar una **cola de prioridad** (heap binario) que entrega siempre el nodo no visitado con menor distancia tentativa.
3. Al extraer un nodo, marcarlo como cerrado y **relajar** sus aristas salientes: si se encuentra un camino más corto a un sucesor, actualizar su distancia y guardar el predecesor.
4. Terminar al cerrar el nodo destino. Reconstruir el camino siguiendo los predecesores hacia atrás.

### 4.2 Por qué respeta los sentidos viales

En cada iteración se exploran únicamente los **sucesores** del nodo actual (`G.successors(u)`), nunca los predecesores. Esto equivale a decir que un vehículo solo puede tomar una calle en el sentido permitido.

### 4.3 Pseudocódigo

```
Dijkstra(G, origen, destino):
    dist[v] ← ∞ para todo v ∈ V
    dist[origen] ← 0
    prev[v] ← null para todo v ∈ V
    Q ← cola de prioridad con (0, origen)
    cerrados ← ∅

    mientras Q no esté vacía:
        (d, u) ← extraer mínimo de Q
        si u ∈ cerrados: continuar
        cerrados ← cerrados ∪ {u}
        si u = destino: terminar

        para cada sucesor v de u (aristas SALIENTES):
            si v ∈ cerrados: continuar
            nuevo ← d + peso(u, v)
            si nuevo < dist[v]:
                dist[v] ← nuevo
                prev[v] ← u
                insertar (nuevo, v) en Q

    reconstruir camino con prev[] desde destino hasta origen
```

---

## 5. Implementación

### 5.1 Librerías

| Librería       | Rol                                                                                   |
| -------------- | ------------------------------------------------------------------------------------- |
| **OSMnx**      | Descarga la red vial de OSM como `MultiDiGraph` con longitudes y sentidos             |
| **NetworkX**   | Estructura del grafo (solo como contenedor; **el Dijkstra está implementado a mano**) |
| **heapq**      | Cola de prioridad de la biblioteca estándar                                           |
| **Matplotlib** | Animación con zoom por rueda del mouse y exportación a PNG                            |
| **Folium**     | Mapa HTML interactivo con tiles de OSM (zoom y panning estilo Google Maps)            |

### 5.2 Etapas del programa

1. **Configuración** — coordenadas de UNAB y UIS, radio del área a descargar (4 km).
2. **Descarga del grafo** — `ox.graph_from_point(centro, dist=4000, network_type='drive')`. El parámetro `network_type='drive'` filtra solo vías transitables en automóvil con sus sentidos.
3. **Snap a la red** — `ox.distance.nearest_nodes` para origen y destino. Imprime un diagnóstico con las coordenadas pedidas, las del nodo elegido y la distancia entre ambos, para verificar visualmente que el snap es correcto.
4. **Dijkstra** — implementación propia con `heapq`. Itera sobre `G.successors(u)` para respetar la dirección. Guarda el orden de cierre de los nodos para luego animar la exploración.
5. **Visualización** — tres salidas (ver sección 8).

### 5.3 Detalle: aristas paralelas

En zonas con calzadas separadas (avenidas con separador central), OSM puede registrar más de una arista entre el mismo par de nodos. Como el grafo es un `MultiDiGraph`, esto se preserva. Para cada par `(u, v)` se selecciona la arista de menor longitud, lo que es coherente con el objetivo de minimizar distancia.

```python
edges = G.get_edge_data(u, v)
w = min(data.get('length', 1.0) for data in edges.values())
```

---

## 6. Resultados

Resultados de la ejecución del prototipo sobre Bucaramanga:

| Métrica                           | Valor                          |
| --------------------------------- | ------------------------------ |
| Nodos del grafo (cruces)          | 3.984                          |
| Aristas del grafo (tramos)        | 8.721                          |
| Tipo de grafo                     | Dirigido (one-ways respetados) |
| Tiempo de descarga del grafo      | ≈ 6 s                          |
| Tiempo de ejecución de Dijkstra   | ≈ 3 ms                         |
| Nodos explorados por el algoritmo | ≈ 1.650                        |
| Nodos en la ruta más corta        | ≈ 29                           |
| **Distancia total UNAB → UIS**    | **≈ 2,2 km**                   |

> Los valores exactos pueden variar ligeramente al cambiar las coordenadas exactas de las entradas o el radio de descarga.

### 6.1 Observaciones

- **Eficiencia del algoritmo:** Dijkstra explora aproximadamente el 41 % de los nodos del grafo antes de cerrar el destino. Esto es típico: al no contar con información sobre la dirección del destino, expande nodos en forma aproximadamente concéntrica desde el origen. Un algoritmo informado como **A\*** con heurística haversine reduciría drásticamente la exploración sin afectar la optimalidad. Ver sección 9.

- **Cuello de botella:** el cálculo de Dijkstra (3 ms) es despreciable frente a la descarga de la red (6 s). En aplicaciones reales el bottleneck es la obtención de los datos, no el algoritmo.

- **Validación:** la ruta obtenida se contrastó visualmente sobre el mapa de OSM y es coherente con un trayecto razonable entre ambas universidades, respetando los sentidos de las vías unidireccionales del corredor.

---

## 7. Cómo ejecutar

### 7.1 Requisitos

- Python 3.10 o superior
- Conexión a internet (solo para la primera ejecución; OSMnx cachea la red localmente después)

### 7.2 Crear entorno virtual e instalar dependencias

```bash
python3 -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 7.3 Ejecución

```bash
python dijkstra_unab_uis.py
```

La primera corrida tarda ~6 s descargando la red vial; las siguientes son inmediatas gracias al caché.

### 7.4 Salida en consola

```
Descargando red vial desde OpenStreetMap...
  Grafo descargado en 6.1s
  Nodos (cruces): 3,984
  Aristas (tramos): 8,721
  Dirigido: True

Verificación de snap a la red vial:
  UNAB:
    coord pedida : (7.11688, -73.10516)
    nodo elegido : ...  (7.11680, -73.10522)
    distancia entre la coord y el nodo: 11 m
  UIS:
    coord pedida : (7.13880, -73.12032)
    nodo elegido : ...  (7.13895, -73.12015)
    distancia entre la coord y el nodo: 25 m

Calculando ruta más corta con Dijkstra...
  Tiempo: 3.1 ms
  Distancia total: 2,241 m  (2.24 km)
  Nodos explorados: 1,651
  Nodos en la ruta: 29
```

---

## 8. Salidas que produce el programa

El programa genera tres visualizaciones complementarias:

### 8.1 Animación en matplotlib

Ventana interactiva que muestra el avance del algoritmo paso a paso: primero crece la nube naranja de nodos explorados, luego se traza la ruta roja. Permite **zoom con la rueda del mouse** centrado en el cursor, y panning con el ícono de la mano de la barra de herramientas.

### 8.2 PNG estática (`dijkstra_unab_uis.png`)

Imagen final con la ruta y los nodos explorados sobre el mapa de calles. Útil para incluir en el documento de entrega.

### 8.3 Mapa HTML interactivo (`ruta_unab_uis.html`)

Mapa estilo Google Maps con tiles reales de OpenStreetMap. Se abre automáticamente en el navegador. Tiene:

- Mapa real con nombres de calles, edificios y referencias.
- Zoom con scroll y panning con drag.
- Marcadores de UNAB (verde) y UIS (azul) con popup informativo al hacer clic.
- Ruta calculada en línea roja sólida.
- **Tramos punteados** desde cada entrada hasta el cruce más cercano del grafo (el "último tramo" mencionado en la sección 3.1).
- Capa toggleable con los nodos explorados por el algoritmo.
- Cuadro flotante con distancia, nodos en la ruta, nodos explorados y tiempo de cálculo.

---

## 9. Limitaciones y posibles mejoras

- **Optimización con A\*:** sustituir Dijkstra por A\* con heurística de distancia haversine al destino reduciría el número de nodos explorados de ≈ 1.650 a unos pocos cientos sin perder optimalidad.

- **Tiempo de viaje en lugar de distancia:** OSMnx puede agregar atributos de velocidad por tipo de vía con `ox.add_edge_speeds(G)` y `ox.add_edge_travel_times(G)`. Cambiando el peso de las aristas de `length` a `travel_time` se obtiene la ruta más rápida en lugar de la más corta.

- **Restricciones de giro:** OSM tiene relaciones de tipo `restriction` (giros prohibidos en intersecciones específicas). El prototipo actual no las usa; incorporarlas requeriría un grafo expandido tipo _line graph_.

- **Datos del Geoportal de Bucaramanga:** si en el futuro la Alcaldía publica la malla vial como GeoJSON o WFS descargable, se podría reemplazar la fuente sin cambiar el algoritmo.

---

## Estructura del proyecto

```
.
├── dijkstra_unab_uis.py          # Script principal
├── requirements.txt              # Dependencias del proyecto
├── .gitignore                    # Archivos excluidos del repositorio
├── readme.md                    # Este archivo
├── dijkstra_unab_uis.png         # (se genera al ejecutar)
└── ruta_unab_uis.html            # (se genera al ejecutar)
```
