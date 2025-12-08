from __future__ import annotations

from typing import Dict, List

import folium

from src.core.vrp import Node, RouteMetrics


COLORS = [
    "red",
    "blue",
    "green",
    "purple",
    "orange",
    "darkred",
    "lightred",
    "beige",
    "darkblue",
    "darkgreen",
    "cadetblue",
    "darkpurple",
]


def render_map(
    depot: Node,
    nodes: Dict[int, Node],
    routes: List[RouteMetrics],
    path: str,
) -> None:
    m = folium.Map(location=[depot.lat, depot.lon], zoom_start=4)
    folium.Marker([depot.lat, depot.lon], popup=f"Depot: {depot.name}", icon=folium.Icon(color="black")).add_to(m)
    for node in nodes.values():
        if node.node_id == depot.node_id:
            continue
        color = "red" if node.priority == 1 else "orange" if node.priority == 2 else "blue"
        folium.CircleMarker(
            [node.lat, node.lon], radius=4, color=color, fill=True, popup=f"{node.name} (p{node.priority})"
        ).add_to(m)

    for idx, route in enumerate(routes):
        color = COLORS[idx % len(COLORS)]
        coords = [[nodes[nid].lat, nodes[nid].lon] for nid in route.sequence]
        folium.PolyLine(coords, color=color, weight=4, opacity=0.8).add_to(m)
    m.save(path)
