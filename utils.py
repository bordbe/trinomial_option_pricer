import plotly.graph_objects as go
import numpy as np


def remove_dupnan(l: list) -> list:
    return list(set(filter(None, l)))


def create_edges_trace(G):
    # edges as disconnected lines in a single trace
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = G.nodes[edge[0]]["pos"]
        x1, y1 = G.nodes[edge[1]]["pos"]
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)
    return go.Scatter(x=edge_x, y=edge_y, line=dict(width=0.5, color="#888"), hoverinfo="none", mode="lines")


def create_nodes_trace(G):
    # nodes as a scatter trace
    node_x = []
    node_y = []
    for node in G.nodes():
        x, y = G.nodes[node]["pos"]
        node_x.append(x)
        node_y.append(y)

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",
        hoverinfo="text",
        marker=dict(
            showscale=True,
            colorscale="Blugrn",
            color=[],
            size=[],
            colorbar=dict(thickness=15, title="Option Value at Node", xanchor="left", titleside="right"),
            line_width=1,
        ),
    )
    return node_trace_options(G, node_trace)


def node_trace_options(G, node_trace):
    node_npv = []
    node_text = []
    node_size = []
    for node in G.nodes():
        size, npv = G.nodes[node]["caract"]
        node_npv.append(npv)
        node_size.append(size)
        node_text.append(f"NPV: {npv:.4f}, Proba: {size:.4f}")

    node_trace.marker.color = node_npv
    node_trace.text = node_text
    node_size = np.asarray(node_size)
    node_trace.marker.size = list(np.interp(node_size, (node_size.min(), node_size.max()), (3, 30)))
    node_trace.marker.line = dict(width=0.5, color="DarkSlateGrey")
    node_trace.marker.opacity = 0.8
    return node_trace


def create_network_graph(G):
    # Add edges as disconnected lines in a single trace and nodes as a scatter trace
    edge_trace = create_edges_trace(G)
    node_trace = create_nodes_trace(G)
    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title="Trinomial Tree",
            titlefont_size=16,
            template="ggplot2",
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=5, r=5, t=40),
            annotations=[dict(text="Bubble size in function of node's reaching probability", showarrow=False, xref="paper", yref="paper", x=0.005, y=-0.002)],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        ),
    )
    return fig
