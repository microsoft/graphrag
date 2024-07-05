# Custom SSL Configuration Mode

---
title: Custom SSL Configuration Mode
navtitle: Custom SSL Config
layout: page
tags: [post]
date: 2024-07-05
---

In certain corporate environments, it is common to have custom root certificates for SSL/TLS communication. This guide explains how to configure `httpx` clients to work with these custom root certificates in GraphRAG.

## Installation

First, you'll need to install the necessary dependencies. Run the following command:

```sh
poetry add httpx[http2] pip-system-certs
```

## Configuration

Below is a sample configuration to set up `httpx` clients with custom SSL certificates:

```python
import httpx
import ssl

# Create a default SSL context and load the system's default certificates
context = ssl.create_default_context()
context.load_default_certs(ssl.Purpose.SERVER_AUTH)  # Load certs for server authentication
verify = context

# Create an httpx client and pass the SSL certificate context
httpx_client = httpx.Client(http2=True, verify=verify)
httpx_client_async = httpx.AsyncClient(http2=True, verify=verify)

# Example of integrating with ChatOpenAI
llm = ChatOpenAI(
    ... # other parameters
    # pass both the synchronous and async clients to the initializer
    http_client=httpx_client,
    http_client_async=httpx_client_async,
)

# Continue remaining code as normal...
```

## Usage

To use the custom SSL configuration, follow these steps:

1. **Install Dependencies**: Run `poetry add httpx[http2] pip-system-certs`.
2. **SSL Configuration**: Use the provided Python script to set up `httpx` clients with custom SSL certificates.
3. **Integration**: Integrate the configured `httpx` clients into your application, as demonstrated above with the `ChatOpenAI` llm.

## Additional Notes

Using custom SSL configurations is an advanced use-case primarily for secure communication in corporate environments with custom root certificates. Most users will not need to modify these settings.

Refer to the [examples](https://github.com/microsoft/graphrag/blob/main/examples/) directory for more details on running different configurations.

---

This custom configuration ensures secure and reliable communication within corporate environments requiring specific SSL/TLS setups.
