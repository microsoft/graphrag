import pandas as pd
from graphrag.index.operations.build_noun_graph.build_noun_graph import _extract_edges

def test_edges_expand_with_singletons():
   
    df = pd.DataFrame(
        {
            "title": ["foo", "bar"],
            "frequency": [1, 1],
            "text_unit_ids": [[1], [1]],
        }
    )
    edges = _extract_edges(df, normalize_edge_weights=False)

    assert len(edges) == 1
    assert set(edges.columns) == {"source", "target", "weight", "text_unit_ids"}
    assert {"foo", "bar"} == set(edges.loc[0, ["source", "target"]]) 