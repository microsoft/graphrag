namespace GraphRag.Config;

public sealed class PruneGraphConfig
{
    public int MinNodeFrequency { get; set; } = 2;

    public double? MaxNodeFrequencyStandardDeviation { get; set; }

    public int MinNodeDegree { get; set; } = 1;

    public double? MaxNodeDegreeStandardDeviation { get; set; }

    public double MinEdgeWeightPercentile { get; set; } = 40.0;

    public bool RemoveEgoNodes { get; set; } = true;

    public bool UseLargestConnectedComponentOnly { get; set; }
}
