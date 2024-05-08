# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing compute_umap_positions and visualize_embedding method definition."""

import graspologic as gc
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import umap

from .typing import NodePosition


def get_zero_positions(
    node_labels: list[str],
    node_categories: list[int] | None = None,
    node_sizes: list[int] | None = None,
    three_d: bool | None = False,
) -> list[NodePosition]:
    """Project embedding vectors down to 2D/3D using UMAP."""
    embedding_position_data: list[NodePosition] = []
    for index, node_name in enumerate(node_labels):
        node_category = 1 if node_categories is None else node_categories[index]
        node_size = 1 if node_sizes is None else node_sizes[index]

        if not three_d:
            embedding_position_data.append(
                NodePosition(
                    label=str(node_name),
                    x=0,
                    y=0,
                    cluster=str(int(node_category)),
                    size=int(node_size),
                )
            )
        else:
            embedding_position_data.append(
                NodePosition(
                    label=str(node_name),
                    x=0,
                    y=0,
                    z=0,
                    cluster=str(int(node_category)),
                    size=int(node_size),
                )
            )
    return embedding_position_data


def compute_umap_positions(
    embedding_vectors: np.ndarray,
    node_labels: list[str],
    node_categories: list[int] | None = None,
    node_sizes: list[int] | None = None,
    min_dist: float = 0.75,
    n_neighbors: int = 25,
    spread: int = 1,
    metric: str = "euclidean",
    n_components: int = 2,
    random_state: int = 86,
) -> list[NodePosition]:
    """Project embedding vectors down to 2D/3D using UMAP."""
    embedding_positions = umap.UMAP(
        min_dist=min_dist,
        n_neighbors=n_neighbors,
        spread=spread,
        n_components=n_components,
        metric=metric,
        random_state=random_state,
    ).fit_transform(embedding_vectors)

    embedding_position_data: list[NodePosition] = []
    for index, node_name in enumerate(node_labels):
        node_points = embedding_positions[index]  # type: ignore
        node_category = 1 if node_categories is None else node_categories[index]
        node_size = 1 if node_sizes is None else node_sizes[index]

        if len(node_points) == 2:
            embedding_position_data.append(
                NodePosition(
                    label=str(node_name),
                    x=float(node_points[0]),
                    y=float(node_points[1]),
                    cluster=str(int(node_category)),
                    size=int(node_size),
                )
            )
        else:
            embedding_position_data.append(
                NodePosition(
                    label=str(node_name),
                    x=float(node_points[0]),
                    y=float(node_points[1]),
                    z=float(node_points[2]),
                    cluster=str(int(node_category)),
                    size=int(node_size),
                )
            )
    return embedding_position_data


def visualize_embedding(
    graph,
    umap_positions: list[dict],
):
    """Project embedding down to 2D using UMAP and visualize."""
    # rendering
    plt.clf()
    figure = plt.gcf()
    ax = plt.gca()

    ax.set_axis_off()
    figure.set_size_inches(10, 10)
    figure.set_dpi(400)

    node_position_dict = {
        (str)(position["label"]): (position["x"], position["y"])
        for position in umap_positions
    }
    node_category_dict = {
        (str)(position["label"]): position["category"] for position in umap_positions
    }
    node_sizes = [position["size"] for position in umap_positions]
    node_colors = gc.layouts.categorical_colors(node_category_dict)  # type: ignore

    vertices = []
    node_color_list = []
    for node in node_position_dict:
        vertices.append(node)
        node_color_list.append(node_colors[node])

    nx.draw_networkx_nodes(
        graph,
        pos=node_position_dict,
        nodelist=vertices,
        node_color=node_color_list,  # type: ignore
        alpha=1.0,
        linewidths=0.01,
        node_size=node_sizes,  # type: ignore
        node_shape="o",
        ax=ax,
    )
    plt.show()
