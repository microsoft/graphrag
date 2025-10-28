namespace GraphRag.Config;

public sealed class LanguageModelConfig
{
    public string? ApiKey { get; set; }

    public AuthType AuthType { get; set; } = AuthType.ApiKey;

    public ModelType Type { get; set; } = ModelType.Chat;

    public string? ModelProvider { get; set; } = "openai";

    public string Model { get; set; } = "gpt-4-turbo-preview";

    public string EncodingModel { get; set; } = "cl100k_base";

    public string? ApiBase { get; set; }

    public string? ApiVersion { get; set; }

    public string? DeploymentName { get; set; }

    public string? Organization { get; set; }

    public string? Proxy { get; set; }

    public string? Audience { get; set; }

    public bool? ModelSupportsJson { get; set; }

    public double RequestTimeout { get; set; } = 120;

    public int? TokensPerMinute { get; set; }

    public int? RequestsPerMinute { get; set; }

    public string? RateLimitStrategy { get; set; }

    public string RetryStrategy { get; set; } = "exponential_backoff";

    public int MaxRetries { get; set; } = 6;

    public double MaxRetryWait { get; set; } = 60;

    public int ConcurrentRequests { get; set; } = 4;

    public AsyncType AsyncMode { get; set; } = AsyncType.AsyncIo;

    public IList<string>? Responses { get; set; }

    public int? MaxTokens { get; set; }

    public double Temperature { get; set; }

    public int? MaxCompletionTokens { get; set; }

    public string? ReasoningEffort { get; set; }

    public double TopP { get; set; } = 1;

    public int N { get; set; } = 1;

    public double FrequencyPenalty { get; set; }

    public double PresencePenalty { get; set; }
}
