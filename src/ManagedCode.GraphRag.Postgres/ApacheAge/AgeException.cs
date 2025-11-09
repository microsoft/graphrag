namespace GraphRag.Storage.Postgres.ApacheAge;

/// <summary>
/// Default and base exception for all exceptions thrown from
/// this library.
/// </summary>
public class AgeException : Exception
{
    /// <summary>
    /// Creates a new instance of <see cref="AgeException"/>.
    /// </summary>
    public AgeException() : base()
    {
    }

    /// <summary>
    /// Creates a new instance of <see cref="AgeException"/> with a specified
    /// error message.
    /// </summary>
    /// <param name="message">
    /// Descriptive error message.
    /// </param>
    public AgeException(string? message)
        : base(message)
    {
    }

    /// <summary>
    /// Creates a new instance of <see cref="AgeException"/> with a specified
    /// error message and the exception that caused this exception to be thrown
    /// as its inner exception.
    /// </summary>
    /// <param name="message">
    /// Descriptive error message.
    /// </param>
    /// <param name="innerException">
    /// Exception that caused this exception to be thrown.
    /// </param>
    public AgeException(string? message, Exception? innerException)
        : base(message, innerException)
    {
    }
}
