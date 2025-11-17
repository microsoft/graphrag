namespace GraphRag.Config;

public sealed class EmbedGraphConfig
{
    public bool Enabled { get; set; }

    public int Dimensions { get; set; } = 1536;

    public int WalkLength { get; set; } = 40;

    public int NumWalks { get; set; } = 10;

    public int WindowSize { get; set; } = 2;

    public int Iterations { get; set; } = 3;

    public int RandomSeed { get; set; } = 597_832;

    public bool UseLargestConnectedComponent { get; set; } = true;
}
