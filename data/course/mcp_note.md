# Model Context Protocol

Model Context Protocol, usually called MCP, is an open protocol that allows systems to provide context and tools to AI models in a standardized way.

## Core Components

MCP usually includes four important parts:

1. Host: the application that the user interacts with, such as Cursor or Claude Desktop.
2. MCP Client: a client library embedded in the host.
3. MCP Server: a lightweight wrapper that exposes tools or data sources.
4. Tool: a callable function, API, local resource, or external service.

## Basic Flow

The client asks the server what tools are available. The server returns tool definitions in a structured format. The host injects tool information into the model context. The user prompt triggers the model to choose a tool. The MCP server executes the tool and returns the result to the model.

## Purpose

MCP reduces the need to build many separate connectors between LLM applications and external tools. It standardizes tool exposure, authentication, data format, and interaction flow.
