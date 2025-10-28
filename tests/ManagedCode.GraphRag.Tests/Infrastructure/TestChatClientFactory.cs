using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;

namespace ManagedCode.GraphRag.Tests.Infrastructure;

internal sealed class TestChatClientFactory
{
    private readonly Func<IReadOnlyList<ChatMessage>, ChatResponse> _responseFactory;

    public TestChatClientFactory(Func<IReadOnlyList<ChatMessage>, ChatResponse>? responseFactory = null)
    {
        _responseFactory = responseFactory ?? (messages => new ChatResponse(new ChatMessage(ChatRole.Assistant, "{}")));
    }

    public IChatClient CreateClient() => new TestChatClient(_responseFactory);

    private sealed class TestChatClient : IChatClient
    {
        private readonly Func<IReadOnlyList<ChatMessage>, ChatResponse> _responseFactory;

        public TestChatClient(Func<IReadOnlyList<ChatMessage>, ChatResponse> responseFactory)
        {
            _responseFactory = responseFactory;
        }

        public void Dispose()
        {
        }

        public Task<ChatResponse> GetResponseAsync(IEnumerable<ChatMessage> messages, ChatOptions? options = null, CancellationToken cancellationToken = default)
        {
            var materialized = messages.ToList().AsReadOnly();
            return Task.FromResult(_responseFactory(materialized));
        }

        public async IAsyncEnumerable<ChatResponseUpdate> GetStreamingResponseAsync(
            IEnumerable<ChatMessage> messages,
            ChatOptions? options = null,
            [EnumeratorCancellation] CancellationToken cancellationToken = default)
        {
            await Task.CompletedTask;
            yield break;
        }

        public object? GetService(Type serviceType, object? serviceKey = null) => null;
    }
}
