namespace GraphRag.Storage.Postgres.ApacheAge.Types;

/// <summary>
/// Graph path.
/// </summary>
public readonly struct Path
{
    /// <summary>
    /// Footer added to the end of every agtype path.
    /// </summary>
    public const string FOOTER = "::path";

    internal Path(object[] path)
    {
        CheckPath(path);

        Length = path.Length / 2;
        Vertices = new Vertex[Length + 1];
        Edges = new Edge[Length];

        for (var i = 0; i < path.Length - 1; i += 2)
        {
            Vertices[i / 2] = (Vertex)path[i];
            Edges[i / 2] = (Edge)path[i + 1];
        }
        Vertices[Length] = (Vertex)path[^1];
    }

    /// <summary>
    /// The length of the path.
    /// </summary>
    /// <remarks>
    /// Equal to the number of edges.
    /// </remarks>
    public int Length { get; }

    /// <summary>
    /// Vertices in the path (in order).
    /// </summary>
    public Vertex[] Vertices { get; }

    /// <summary>
    /// Edges in the path.
    /// </summary>
    /// <remarks>
    /// Edge with index 0 is the edge between vertices 0 and 1. Edge 1
    /// connects vertices 1 and 2, and so on.
    /// </remarks>
    public Edge[] Edges { get; }

    private static void CheckPath(object[] path)
    {
        for (var i = 0; i < path.Length; i++)
        {
            var shouldBeVertex = i % 2 == 0;

            if (shouldBeVertex && path[i].GetType() != typeof(Vertex))
            {
                throw new FormatException("Invalid path");
            }
            if (!shouldBeVertex && path[i].GetType() != typeof(Edge))
            {
                throw new FormatException("Invalid path");
            }
        }
    }
}
