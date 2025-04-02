# Visualizing and Debugging Your Knowledge Graph

The following step-by-step guide walks through the process to visualize a knowledge graph after it's been constructed by graphrag. Note that some of the settings recommended below are based on our own experience of what works well. Feel free to change and explore other settings for a better visualization experience!

## 1. Run the Pipeline
Before building an index, please review your `settings.yaml` configuration file and ensure that graphml snapshots is enabled.
```yaml
snapshots:
  graphml: true
```
(Optional) To support other visualization tools and exploration, additional parameters can be enabled that provide access to vector embeddings.
```yaml
embed_graph:
  enabled: true # will generate node2vec embeddings for nodes
umap:
  enabled: true # will generate UMAP embeddings for nodes, giving the entities table an x/y position to plot
```
After running the indexing pipeline over your data, there will be an output folder (defined by the `storage.base_dir` setting).

- **Output Folder**: Contains artifacts from the LLM’s indexing pass.

## 2. Locate the Knowledge Graph
In the output folder, look for a file named `graph.graphml`. graphml is a standard [file format](http://graphml.graphdrawing.org) supported by many visualization tools. We recommend trying [Gephi](https://gephi.org).

## 3. Open the Graph in Gephi
1. Install and open Gephi
2. Navigate to the `output` folder containing the various parquet files.
3. Import the `graph.graphml` file into Gephi. This will result in a fairly plain view of the undirected graph nodes and edges.

<p align="center">
   <img src="../img/viz_guide/gephi-initial-graph-example.png" alt="A basic graph visualization by Gephi" width="300"/>
</p>

## 4. Install the Leiden Algorithm Plugin
1. Go to `Tools` -> `Plugins`.
2. Search for "Leiden Algorithm".
3. Click `Install` and restart Gephi.

## 5. Run Statistics
1. In the `Statistics` tab on the right, click `Run` for `Average Degree` and `Leiden Algorithm`.

<p align="center">
   <img src="../img/viz_guide/gephi-network-overview-settings.png" alt="A view of Gephi's network overview settings" width="300"/>
</p>

2. For the Leiden Algorithm, adjust the settings:
   - **Quality function**: Modularity
   - **Resolution**: 1

## 6. Color the Graph by Clusters
1. Go to the `Appearance` pane in the upper left side of Gephi.

<p align="center">
   <img src="../img/viz_guide/gephi-appearance-pane.png" alt="A view of Gephi's appearance pane" width="500"/>
</p>

2. Select `Nodes`, then `Partition`, and click the color palette icon in the upper right.
3. Choose `Cluster` from the dropdown.
4. Click the `Palette...` hyperlink, then `Generate...`.
5. Uncheck `Limit number of colors`, click `Generate`, and then `Ok`.
6. Click `Apply` to color the graph. This will color the graph based on the partitions discovered by Leiden.

## 7. Resize Nodes by Degree Centrality
1. In the `Appearance` pane in the upper left, select `Nodes` -> `Ranking`
2. Select the `Sizing` icon in the upper right.
2. Choose `Degree` and set:
   - **Min**: 10
   - **Max**: 150
3. Click `Apply`.

## 8. Layout the Graph
1. In the `Layout` tab in the lower left, select `OpenORD`.

<p align="center">
   <img src="../img/viz_guide/gephi-layout-pane.png" alt="A view of Gephi's layout pane" width="400"/>
</p>

2. Set `Liquid` and `Expansion` stages to 50, and everything else to 0.
3. Click `Run` and monitor the progress.

## 9. Run ForceAtlas2
1. Select `Force Atlas 2` in the layout options.

<p align="center">
   <img src="../img/viz_guide/gephi-layout-forceatlas2-pane.png" alt="A view of Gephi's ForceAtlas2 layout pane" width="400"/>
</p>

2. Adjust the settings:
   - **Scaling**: 15
   - **Dissuade Hubs**: checked
   - **LinLog mode**: uncheck
   - **Prevent Overlap**: checked
3. Click `Run` and wait.
4. Press `Stop` when it looks like the graph nodes have settled and no longer change position significantly.

## 10. Add Text Labels (Optional)
1. Turn on text labels in the appropriate section.
2. Configure and resize them as needed.

Your final graph should now be visually organized and ready for analysis!
