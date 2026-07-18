# 可视化和调试你的知识图谱

以下分步指南将引导你完成在 graphrag 构建知识图谱之后对其进行可视化的过程。请注意，下面推荐的某些设置是基于我们自身对哪些设置效果较好的经验。你可以随意调整并探索其他设置，以获得更好的可视化体验！

## 1. 运行流水线
在构建索引之前，请查看你的 `settings.yaml` 配置文件，并确保已启用 graphml 快照。
```yaml
snapshots:
  graphml: true
```
在对你的数据运行索引流水线后，将会有一个输出文件夹（由 `storage.base_dir` 设置定义）。

- **输出文件夹**：包含来自 LLM 索引过程的产物。

## 2. 定位知识图谱
在输出文件夹中，查找名为 `graph.graphml` 的文件。graphml 是一种标准的[文件格式](http://graphml.graphdrawing.org)，受到许多可视化工具的支持。我们建议尝试使用 [Gephi](https://gephi.org)。

## 3. 在 Gephi 中打开图谱
1. 安装并打开 Gephi
2. 导航到包含各种 parquet 文件的 `output` 文件夹。
3. 将 `graph.graphml` 文件导入 Gephi。这将得到一个相当朴素的无向图节点和边的视图。

<p align="center">
   <img src="../../img/viz_guide/gephi-initial-graph-example.png" alt="Gephi 生成的基础图可视化" width="300"/>
</p>

## 4. 安装 Leiden Algorithm 插件
1. 前往 `Tools` -> `Plugins`。
2. 搜索“Leiden Algorithm”。
3. 点击 `Install` 并重启 Gephi。

## 5. 运行统计
1. 在右侧的 `Statistics` 选项卡中，点击 `Average Degree` 和 `Leiden Algorithm` 的 `Run`。

<p align="center">
   <img src="../../img/viz_guide/gephi-network-overview-settings.png" alt="Gephi 网络概览设置视图" width="300"/>
</p>

2. 对于 Leiden Algorithm，调整设置：
   - **质量函数**：Modularity
   - **分辨率**：1

## 6. 按聚类为图谱着色
1. 前往 Gephi 左上角的 `Appearance` 面板。

<p align="center">
   <img src="../../img/viz_guide/gephi-appearance-pane.png" alt="Gephi 外观面板视图" width="500"/>
</p>

2. 选择 `Nodes`，然后选择 `Partition`，并点击右上角的调色板图标。
3. 从下拉菜单中选择 `Cluster`。
4. 点击 `Palette...` 超链接，然后点击 `Generate...`。
5. 取消勾选 `Limit number of colors`，点击 `Generate`，然后点击 `Ok`。
6. 点击 `Apply` 为图谱着色。这将根据 Leiden 发现的分区为图谱着色。

## 7. 按度中心性调整节点大小
1. 在左上角的 `Appearance` 面板中，选择 `Nodes` -> `Ranking`
2. 选择右上角的 `Sizing` 图标。
2. 选择 `Degree` 并设置：
   - **最小值**：10
   - **最大值**：150
3. 点击 `Apply`。

## 8. 布局图谱
1. 在左下角的 `Layout` 选项卡中，选择 `OpenORD`。

<p align="center">
   <img src="../../img/viz_guide/gephi-layout-pane.png" alt="Gephi 布局面板视图" width="400"/>
</p>

2. 将 `Liquid` 和 `Expansion` 阶段设置为 50，其他全部设置为 0。
3. 点击 `Run` 并监控进度。

## 9. 运行 ForceAtlas2
1. 在布局选项中选择 `Force Atlas 2`。

<p align="center">
   <img src="../../img/viz_guide/gephi-layout-forceatlas2-pane.png" alt="Gephi 的 ForceAtlas2 布局面板视图" width="400"/>
</p>

2. 调整设置：
   - **缩放**：15
   - **抑制枢纽**：勾选
   - **LinLog 模式**：取消勾选
   - **防止重叠**：勾选
3. 点击 `Run` 并等待。
4. 当图节点看起来已经稳定且位置不再发生明显变化时，按下 `Stop`。

## 10. 添加文本标签（可选）
1. 在相应部分打开文本标签。
2. 根据需要对其进行配置和调整大小。

现在，你的最终图谱应该已经在视觉上组织良好，并可用于分析！