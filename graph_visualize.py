
import networkx as nx
import plotly.graph_objects as go
import plotly.offline as pyo


def visualize_graph_plotly(graph, route=None, title="Warehouse Map"):
    """Generate interactive Plotly visualization of the graph."""
    G = nx.Graph()

    # Add weighted edges
    for node, neighbors in graph.items():
        print(node, neighbors)
        for neighbor, weight in neighbors.items():
            G.add_edge(node, neighbor, weight=weight)

    pos = nx.spring_layout(G, seed=42)

    # Create edge traces
    edge_x = []
    edge_y = []
    edge_text = []
    for edge in G.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_text.append(f"{edge[2]['weight']}")

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=2, color='gray'),
        hoverinfo='text',
        text=edge_text,
        mode='lines'
    )

    # Highlight route edges if provided
    if route:
        route_edge_x = []
        route_edge_y = []
        route_edges = list(zip(route, route[1:]))
        for u, v in route_edges:
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            route_edge_x.extend([x0, x1, None])
            route_edge_y.extend([y0, y1, None])

        route_edge_trace = go.Scatter(
            x=route_edge_x, y=route_edge_y,
            line=dict(width=4, color='red'),
            hoverinfo='skip',
            mode='lines'
        )

    # Create node traces
    node_x = []
    node_y = []
    node_text = []
    node_color = []
    node_custom_text = []  # For display text
    
    # Create a mapping of node to its order in the route
    route_order = {}
    if route:
        for idx, node in enumerate(route):
            if node not in route_order:  # First occurrence
                route_order[node] = idx
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)
        
        if route and node in route_order:
            node_color.append('gold')
            # Add order number to display
            node_custom_text.append(f"<b>#{route_order[node]}</b><br>{node}")
        else:
            node_color.append('lightblue')
            node_custom_text.append(node)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=node_custom_text,
        textposition="middle center",
        textfont=dict(size=12, color='black'),
        hoverinfo='text',
        hovertext=node_text,
        marker=dict(
            showscale=False,
            color=node_color,
            size=30 if route else 20,
            line_width=2,
            line_color='darkgray'
        )
    )

    # Create figure
    fig = go.Figure(data=[edge_trace, node_trace])
    if route:
        fig.add_trace(route_edge_trace)

    fig.update_layout(
        title=title,
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
    )

    return pyo.plot(fig, output_type='div', include_plotlyjs=True)
