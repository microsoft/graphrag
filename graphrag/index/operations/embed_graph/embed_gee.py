# Copyright (c) 2024 Microsoft Corporation. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#
import logging
from dataclasses import dataclass

import networkx as nx
import numpy as np
from scipy import sparse
from scipy.sparse import linalg
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize

logger = logging.getLogger(__name__)

# invalid divide results will be nan
np.seterr(divide="ignore", invalid="ignore")


@dataclass
class NodeEmbeddings:
    """Node embeddings class definition."""

    nodes: list[str]
    embeddings: np.ndarray


def _basic(x, y, n):
    """
    Graph embedding basic function.

    Input X is sparse csr matrix of adjacency matrix
    -- if there is a connection between node i and node j:
    ---- X(i,j) = 1, no edge weight
    ---- X(i,j) = edge weight.
    -- if there is no connection between node i and node j:
    ---- X(i,j) = 0,
    ---- note there is no storage for this in sparse matrix.
    ---- No storage means 0 in sparse matrix.
    input Y is numpy array with size (n,1):
    -- value -1 indicate no label
    -- value >=0 indicate real label
    input train_idx: a list of indices of input X for training set
    """
    # assign k to the max along the first column
    # Note for python, label y starts from 0. Python index starts from 0. thus size k should be max + 1
    k = y[:, 0].max() + 1

    # nk: 1*n array, contains the number of observations in each class
    nk = np.zeros((1, k))
    for i in range(k):
        nk[0, i] = np.count_nonzero(y[:, 0] == i)

    # W: sparse matrix for encoder matrix. w[i,k] = {1/nk if yi==k, otherwise 0}
    w = sparse.dok_matrix((n, k), dtype=np.float32)

    for i in range(n):
        k_i = y[i, 0]
        if k_i >= 0:
            w[i, k_i] = 1 / nk[0, k_i]

    w = sparse.csr_matrix(w)
    return x.dot(w)


def _diagonal(x, n):
    """
    Graph embedding diagonal function.

    Input X is sparse csr matrix of adjacency matrix
    return a sparse csr matrix of X matrix with 1s on the diagonal
    """
    i = sparse.identity(n)
    return x + i


def _laplacian(x):
    """
    Graph embedding Laplacian function.

    Input X is sparse csr matrix of adjacency matrix
    return a sparse csr matrix of Laplacian normalization of X matrix
    """
    x_sparse = sparse.csr_matrix(x)
    # get an array of degrees
    dig = x_sparse.sum(axis=0).A1
    # diagonal sparse matrix of D
    d = sparse.diags(dig, 0)
    d_pow = d.power(-0.5)
    return d_pow.dot(x_sparse.dot(d_pow))


def _correlation(z):
    """
    Graph embedding correlation function.

    Input Z is sparse csr matrix of embedding matrix from the basic function
    return normalized Z sparse matrix
    Calculation:
    Calculate each row's 2-norm (Euclidean distance).
    e.g.row_x: [ele_i,ele_j,ele_k]. norm2 = sqr(sum(ele_i^2+ele_i^2+ele_i^2))
    then divide each element by their row norm
    e.g. [ele_i/norm2,ele_j/norm2,ele_k/norm2]
    """
    # 2-norm
    row_norm = linalg.norm(z, axis=1)

    # row division to get the normalized Z
    diag = np.nan_to_num(1 / row_norm)
    n = sparse.diags(diag, 0)
    return n.dot(z)


def _edge_list_size(x):
    """
    Get the edge list size flag.

    set default edge list size as S3.
    If find x only has 2 columns,
    return a flag "S2" indicating this is S2 edge list
    """
    # check the first entry to see if it is 2 or 3
    if len(x[0]) == 2:
        return "S2"

    return "S3"


def _edge_to_sparse(x, n, size_flag):
    """
    Convert edge list to sparse matrix.

    input X is an edge list.
    For S2 edge list (e.g. node_i, node_j per row), add one to all connections
    return a sparse csr matrix of S3 edge list
    """
    # Build an empty sparse matrix.
    x_new = sparse.dok_matrix((n, n), dtype=np.float32)

    for row in x:
        if size_flag == "S2":
            [node_i, node_j] = [int(row[0]), int(row[1])]
            x_new[node_i, node_j] = 1
        else:
            [node_i, node_j, weight] = [int(row[0]), int(row[1]), float(row[2])]
            x_new[node_i, node_j] = weight

    return sparse.csr_matrix(x_new)


def _get_edge_list(graph, node_list):
    """Generate a list of edges with weights for existing nodes."""
    node_to_ix = {node: i for i, node in enumerate(node_list)}
    return [
        [node_to_ix[s], node_to_ix[t], w]
        for s, t, w in graph.edges(data="weight")
        if s in node_list and t in node_list
    ]


def _run_gee(
    x,
    y,
    n,
    check_edge_list=False,
    diag_a=True,
    laplacian=False,
    correlation=True,
):
    if check_edge_list:
        size_flag = _edge_list_size(x)
        x = _edge_to_sparse(x, n, size_flag)

    if diag_a:
        x = _diagonal(x, n)

    if laplacian:
        x = _laplacian(x)

    z = _basic(x, y, n)

    if correlation:
        z = _correlation(z)

    return z


def embed_gee(
    graph: nx.Graph, node_to_label, correlation, diag_a, laplacian, max_level
) -> NodeEmbeddings:
    """Generate embeddings using graph encoder embedder."""
    node_list = sorted(node_to_label.keys())
    edge_list = _get_edge_list(graph, node_list)
    num_nodes = len(node_list)

    node_to_ix = {node: i for i, node in enumerate(node_list)}

    # Note that this function relies upon the incoming node_to_label dictionary to be FULL and complete.  Every node MUST be defined for EVERY level in the hierarchy.
    # When a node doesn't technically exist, make sure that it is populated with the leaf level parent for the logic below to work.

    level_embeddings = {}
    # For each level
    for level in range(max_level + 1):
        labels = np.array([
            node_to_label[node][level] if node in node_to_label else -1
            for node in node_list
        ]).reshape((
            num_nodes,
            1,
        ))
        vectors = _run_gee(
            edge_list,
            labels,
            num_nodes,
            check_edge_list=True,
            laplacian=laplacian,
            diag_a=diag_a,
            correlation=correlation,
        )
        level_embeddings[level] = vectors

    # Now create a joint embedding across all levels
    # get the length of any vector at the root level - this is the minimal number of dimensions to PCA to
    # and resize all vectors to be of this same length.
    embedding_length = level_embeddings[0].shape[1]

    normalized_vectors = {}

    for level in range(max_level + 1):
        # First check to see if we should PCA the whole thing first to a standard dimensionality
        # Obviously for root level 0 - nothing needs to be done
        if level_embeddings[level].shape[1] == embedding_length:
            # at the root level, just copy the vectors over
            normalized_vectors[level] = normalize(level_embeddings[level].toarray())

        else:
            # ideally we actually run a PCA, but that doesn't scale - so we instead use a TSVD
            tsvd = TruncatedSVD(n_components=embedding_length)

            tsvd.fit(level_embeddings[level].toarray())

            normalized_vectors[level] = normalize(
                tsvd.transform(level_embeddings[level].toarray())
            )

    concat_vectors = {}
    # Next, ONLY copy over the nodes that actually exist at a given level
    for node in node_list:
        for level in range(max_level + 1):
            if level not in concat_vectors:
                concat_vectors[level] = {}
            # Check to see if the node actually existed natively at this level of the hierarchy - otherwise we can take alternative logic - like zeroing out this part of the vector.
            if level == 0:
                # First, all nodes exist at 0
                concat_vectors[level][node] = normalized_vectors[level][
                    node_to_ix[node]
                ]
            else:
                # Deeper the level 0, we have to check if the node actually exists at this level
                if node_to_label[node][level - 1] != node_to_label[node][level]:
                    # the node existed at this depth of the hierarchy
                    concat_vectors[level][node] = normalized_vectors[level][
                        node_to_ix[node]
                    ]
                else:
                    # if the node has the SAME cluster ID as its parent, then we know it doesn't actually at this level in the hierarchy
                    # So this zeros out the vector if it didn't exist at level of the hierarchy.... we can zero it out OR we can use the cluster membership from the tiers above and then keep the embedding
                    concat_vectors[level][node] = [0] * embedding_length

    node_vectors = []
    # next - concat all the vectors together for all layers of the hierarchy
    for node in node_list:
        node_vector = []
        for level in range(max_level + 1):
            node_vector = np.append(node_vector, concat_vectors[level][node])
        node_vectors.append(np.array(node_vector))
    node_array = np.vstack(node_vectors)

    return normalize(node_array)
