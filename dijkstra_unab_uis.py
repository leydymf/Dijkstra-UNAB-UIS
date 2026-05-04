"""
Prototipo visual del algoritmo de Dijkstra
Ruta más corta UNAB -> UIS sobre la red vial real de Bucaramanga.

Genera tres salidas:
  1) Animación en matplotlib (con zoom por rueda del mouse)
  2) PNG estática con la ruta final
  3) Mapa HTML interactivo con folium (zoom y panning estilo Google Maps)

Dependencias:
    pip install osmnx matplotlib folium
"""

import heapq
import time
import webbrowser
from pathlib import Path

import osmnx as ox
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.lines import Line2D
import folium

# ---------------------------------------------------------------------------
# 1. CONFIGURACIÓN
# ---------------------------------------------------------------------------

# Coordenadas oficiales de OpenStreetMap (lat, lon)
UNAB_COORDS = (7.11688, -73.10516)  # Campus El Jardín, Av. 42
UIS_COORDS = (7.13880, -73.12032)  # Portería principal Cra. 27

CENTRO = ((UNAB_COORDS[0] + UIS_COORDS[0]) / 2, (UNAB_COORDS[1] + UIS_COORDS[1]) / 2)
RADIO_M = 4000  # 4 km

ANIMAR = True  # animación matplotlib
ABRIR_HTML = True  # abre el mapa interactivo automáticamente


# ---------------------------------------------------------------------------
# 2. DESCARGA DE LA RED VIAL
# ---------------------------------------------------------------------------

print("Descargando red vial desde OpenStreetMap...")
t0 = time.time()
G = ox.graph_from_point(CENTRO, dist=RADIO_M, network_type="drive")
G = ox.distance.add_edge_lengths(G)
print(f"  Grafo descargado en {time.time()-t0:.1f}s")
print(f"  Nodos (cruces): {len(G.nodes):,}")
print(f"  Aristas (tramos): {len(G.edges):,}")
print(f"  Dirigido: {G.is_directed()}")


# ---------------------------------------------------------------------------
# 3. NODOS DE PARTIDA Y LLEGADA
# ---------------------------------------------------------------------------

orig = ox.distance.nearest_nodes(G, X=UNAB_COORDS[1], Y=UNAB_COORDS[0])
dest = ox.distance.nearest_nodes(G, X=UIS_COORDS[1], Y=UIS_COORDS[0])


def diagnostico(nombre, coords_pedidas, nodo):
    nx_, ny_ = G.nodes[nodo]["x"], G.nodes[nodo]["y"]
    d = ox.distance.great_circle(coords_pedidas[0], coords_pedidas[1], ny_, nx_)
    print(f"  {nombre}:")
    print(f"    coord pedida : ({coords_pedidas[0]:.5f}, {coords_pedidas[1]:.5f})")
    print(f"    nodo elegido : {nodo}  ({ny_:.5f}, {nx_:.5f})")
    print(f"    distancia entre la coord y el nodo: {d:.0f} m")


print("\nVerificación de snap a la red vial:")
diagnostico("UNAB", UNAB_COORDS, orig)
diagnostico("UIS", UIS_COORDS, dest)


# ---------------------------------------------------------------------------
# 4. DIJKSTRA (implementación propia)
# ---------------------------------------------------------------------------


def dijkstra(G, source, target):
    dist = {source: 0.0}
    prev = {source: None}
    visited = set()
    heap = [(0.0, source)]
    visit_order = []

    while heap:
        d, u = heapq.heappop(heap)
        if u in visited:
            continue
        visited.add(u)
        visit_order.append(u)
        if u == target:
            break
        for v in G.successors(u):  # respeta one-ways
            if v in visited:
                continue
            edges = G.get_edge_data(u, v)
            w = min(data.get("length", 1.0) for data in edges.values())
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, v))

    if target not in dist:
        raise RuntimeError("No existe ruta dirigida entre UNAB y UIS.")

    path = []
    cur = target
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    return list(reversed(path)), dist[target], visit_order


print("\nCalculando ruta más corta con Dijkstra...")
t0 = time.time()
path, cost, visit_order = dijkstra(G, orig, dest)
tiempo_dijkstra = (time.time() - t0) * 1000
print(f"  Tiempo: {tiempo_dijkstra:.1f} ms")
print(f"  Distancia total: {cost:,.0f} m  ({cost/1000:.2f} km)")
print(f"  Nodos explorados: {len(visit_order):,}")
print(f"  Nodos en la ruta: {len(path):,}")


# ---------------------------------------------------------------------------
# 5. MAPA HTML INTERACTIVO CON FOLIUM (zoom y panning reales)
# ---------------------------------------------------------------------------

print("\nGenerando mapa HTML interactivo...")

m = folium.Map(location=CENTRO, zoom_start=15, tiles="OpenStreetMap")

route_latlon = [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in path]

folium.PolyLine(
    route_latlon,
    color="#e74c3c",
    weight=6,
    opacity=0.85,
    tooltip=f"Ruta más corta — {cost/1000:.2f} km, {len(path)} cruces",
).add_to(m)

# Tramos punteados desde la entrada real hasta el primer/último nodo del grafo
# (la entrada de cada universidad no es un cruce, así que el grafo no la incluye)
folium.PolyLine(
    [UNAB_COORDS, (G.nodes[orig]["y"], G.nodes[orig]["x"])],
    color="#2ecc71",
    weight=3,
    opacity=0.8,
    dash_array="6, 8",
    tooltip="Tramo entrada UNAB → primer cruce",
).add_to(m)
folium.PolyLine(
    [(G.nodes[dest]["y"], G.nodes[dest]["x"]), UIS_COORDS],
    color="#3498db",
    weight=3,
    opacity=0.8,
    dash_array="6, 8",
    tooltip="Tramo último cruce → portería UIS",
).add_to(m)

explored_layer = folium.FeatureGroup(
    name=f"Nodos explorados ({len(visit_order)})", show=False
)
for n in visit_order:
    folium.CircleMarker(
        location=(G.nodes[n]["y"], G.nodes[n]["x"]),
        radius=2,
        color="#f39c12",
        fill=True,
        fill_opacity=0.6,
        weight=0,
    ).add_to(explored_layer)
explored_layer.add_to(m)

folium.Marker(
    location=UNAB_COORDS,
    popup="<b>UNAB</b><br>Inicio (Campus El Jardín)",
    tooltip="UNAB — Inicio",
    icon=folium.Icon(color="green", icon="play", prefix="fa"),
).add_to(m)

folium.Marker(
    location=UIS_COORDS,
    popup="<b>UIS</b><br>Destino (Sede Central)",
    tooltip="UIS — Destino",
    icon=folium.Icon(color="blue", icon="flag", prefix="fa"),
).add_to(m)

resumen_html = f"""
<div style="position: fixed; bottom: 20px; left: 20px; z-index: 9999;
            background: white; padding: 12px 16px; border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            font-family: Arial, sans-serif; font-size: 13px;">
  <b style="font-size: 14px;">Dijkstra UNAB → UIS</b><br>
  Distancia: <b>{cost/1000:.2f} km</b><br>
  Cruces en la ruta: <b>{len(path)}</b><br>
  Nodos explorados: <b>{len(visit_order):,}</b> de {len(G.nodes):,}<br>
  Tiempo de cálculo: <b>{tiempo_dijkstra:.1f} ms</b>
</div>
"""
m.get_root().html.add_child(folium.Element(resumen_html))
folium.LayerControl(collapsed=False).add_to(m)

html_path = Path("ruta_unab_uis.html").resolve()
m.save(str(html_path))
print(f"  Guardado: {html_path}")


# ---------------------------------------------------------------------------
# 6. VISUALIZACIÓN MATPLOTLIB CON ZOOM POR RUEDA
# ---------------------------------------------------------------------------

xs = {n: G.nodes[n]["x"] for n in G.nodes}
ys = {n: G.nodes[n]["y"] for n in G.nodes}

fig, ax = ox.plot_graph(
    G,
    node_size=0,
    edge_color="#cccccc",
    edge_linewidth=0.6,
    bgcolor="white",
    show=False,
    close=False,
)

ax.scatter(xs[orig], ys[orig], s=220, c="#2ecc71", edgecolors="black", zorder=6)
ax.scatter(xs[dest], ys[dest], s=220, c="#3498db", edgecolors="black", zorder=6)

explored_scatter = ax.scatter([], [], s=4, c="#f39c12", alpha=0.6, zorder=3)

route_xs = [xs[n] for n in path]
route_ys = [ys[n] for n in path]
(route_line,) = ax.plot([], [], color="#e74c3c", linewidth=3.5, zorder=5)

# Tramos punteados entrada-cruce (la entrada no es un nodo del grafo)
ax.plot(
    [UNAB_COORDS[1], xs[orig]],
    [UNAB_COORDS[0], ys[orig]],
    linestyle="--",
    color="#2ecc71",
    linewidth=2,
    alpha=0.8,
    zorder=4,
)
ax.plot(
    [xs[dest], UIS_COORDS[1]],
    [ys[dest], UIS_COORDS[0]],
    linestyle="--",
    color="#3498db",
    linewidth=2,
    alpha=0.8,
    zorder=4,
)

ax.set_title(
    f"Dijkstra UNAB → UIS    {cost/1000:.2f} km    "
    f"{len(visit_order):,} nodos explorados\n"
    f"(rueda del mouse = zoom; barra de matplotlib = pan)",
    fontsize=11,
)

legend_elems = [
    Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        markerfacecolor="#2ecc71",
        markeredgecolor="black",
        markersize=10,
        label="UNAB (inicio)",
    ),
    Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        markerfacecolor="#3498db",
        markeredgecolor="black",
        markersize=10,
        label="UIS (destino)",
    ),
    Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        markerfacecolor="#f39c12",
        markersize=6,
        label="Nodos explorados",
    ),
    Line2D([0], [0], color="#e74c3c", linewidth=3, label="Ruta más corta"),
]
ax.legend(handles=legend_elems, loc="lower left", fontsize=9)


# Zoom con rueda del mouse, centrado en el cursor
def on_scroll(event):
    if event.inaxes != ax:
        return
    cur_xlim = ax.get_xlim()
    cur_ylim = ax.get_ylim()
    xdata, ydata = event.xdata, event.ydata
    if xdata is None or ydata is None:
        return
    if event.button == "up":
        scale = 1 / 1.3
    elif event.button == "down":
        scale = 1.3
    else:
        return
    new_w = (cur_xlim[1] - cur_xlim[0]) * scale
    new_h = (cur_ylim[1] - cur_ylim[0]) * scale
    relx = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])
    rely = (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])
    ax.set_xlim([xdata - new_w * (1 - relx), xdata + new_w * relx])
    ax.set_ylim([ydata - new_h * (1 - rely), ydata + new_h * rely])
    fig.canvas.draw_idle()


fig.canvas.mpl_connect("scroll_event", on_scroll)


if ANIMAR:
    step = max(1, len(visit_order) // 120)
    explore_frames = list(range(0, len(visit_order), step)) + [len(visit_order)]
    n_explore = len(explore_frames)
    n_route = 60
    total = n_explore + n_route

    def update(i):
        if i < n_explore:
            k = explore_frames[i]
            pts = [(xs[n], ys[n]) for n in visit_order[:k]]
            explored_scatter.set_offsets(pts if pts else [[None, None]])
        else:
            j = i - n_explore + 1
            cut = max(2, int(len(path) * j / n_route))
            route_line.set_data(route_xs[:cut], route_ys[:cut])
        return explored_scatter, route_line

    anim = FuncAnimation(
        fig, update, frames=total, interval=40, blit=False, repeat=False
    )
else:
    explored_scatter.set_offsets([(xs[n], ys[n]) for n in visit_order])
    route_line.set_data(route_xs, route_ys)

plt.tight_layout()
plt.savefig("dijkstra_unab_uis.png", dpi=150, bbox_inches="tight")

if ABRIR_HTML:
    webbrowser.open(html_path.as_uri())

plt.show()
