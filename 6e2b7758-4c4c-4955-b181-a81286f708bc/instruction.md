# Implement `Neoteroi/BlackSheep`

You are given a Python repository at `/testbed`, reset to a skeleton commit: every function body has been replaced with a `pass` statement.

You need to complete the implementations for all functions (i.e., those with `pass` statements) and pass the unit tests.
Do not change the names of existing functions or classes, as they may be referenced from other code like unit tests, etc.
When you generate code, you must maintain the original formatting of the original function stubs (such as whitespaces), otherwise we will not be able to search/replace blocks for code modifications, and therefore you will receive a score of 0 for your generated code.

## Repository details

- Upstream project: `Neoteroi/BlackSheep`
- Source directory to implement: `blacksheep/`
- Test command: `pytest` (run against `tests`)
- Specification / docs: https://www.neoteroi.dev/blacksheep/

Implement only the library source under the source directory. Do not modify the test files.

>>> Here is the Specification Information:

BlackSheep https://github.com/Neoteroi/BlackSheep BlackSheep is an asynchronous web framework to build event based web applications with Python. It is inspired by Flask, ASP.NET Core, and the work by Yury Selivanov.

Installation pip install blacksheep Quick example: from datetime import datetime, timezone from blacksheep import Application, get app = Application() @get("/") async def home(): return f"Hello, World! {datetime.now(timezone.utc).isoformat()}" Getting started using the CLI BlackSheep offers a CLI to bootstrap new projects rapidly. To try it, first install the blacksheep-cli package: pip install blacksheep-cli Then use the blacksheep create command to bootstrap a project using one of the supported templates. The CLI includes a help, and supports custom templates, using the same sources supported by Cookiecutter.

Dependencies Before version 2.3.1, BlackSheep only supported running with CPython and always depended on httptools.

Starting with version 2.3.1, the framework supports running on PyPy and makes httptools an optional dependency. Since version 2.5.0, the BlackSheep HTTP Client includes HTTP/2 support and requires h11 and h2 libraries. For slightly better performance in URL parsing when running on CPython, it is recommended to install httptools (optional). The best performance can be achieved using PyPy runtime, and Socketify or Granian.

Requirements Python: any version listed in the project's classifiers. BlackSheep belongs to the category of ASGI web frameworks, so it requires an ASGI HTTP server to run, such as uvicorn, hypercorn or granian. For example, to use it with uvicorn: pip install uvicorn uvicorn server:app Automatic bindings and dependency injection BlackSheep supports automatic binding of values for request handlers, by type annotation or by conventions. It supports binding of JSON payloads to dataclasses (FromJSON), query parameters (FromQuery) with default values, and route parameters by matching names. It also supports dependency injection, a feature that provides a consistent and clean way to use dependencies in request handlers.

Authentication and Authorization BlackSheep implements strategies to handle authentication and authorization. It provides built-in support for OpenID Connect authentication and JWT Bearer authentication, meaning it is easy to integrate with services such as Auth0, Microsoft Entra ID, Azure Active Directory B2C, and Okta. Since version 2.4.2, it also offers built-in support for Basic authentication, API Key authentication, JWT Bearer authentication using symmetric encryption, and automatic generation of OpenAPI Documentation for security schemes.

Web framework features ASGI compatibility. Routing. Request handlers can be defined as functions or class methods. Middlewares.

WebSocket. Server-Sent Events (SSE). Built-in support for dependency injection. Support for automatic binding of route and query parameters to request handler method calls. Strategy to handle exceptions. Strategy to handle authentication and authorization. Handlers normalization. Serving static files. Integration with Jinja2.

Support for serving SPAs that use HTML5 History API. Support for automatic generation of OpenAPI Documentation. Strategy to handle CORS settings. Sessions. Support for automatic binding of dataclasses and Pydantic models to handle the request body payload. TestClient class to simplify testing of applications. Anti Forgery validation to protect against Cross-Site Request Forgery (XSRF/CSRF) attacks.

Client features BlackSheep includes an HTTP Client with native HTTP/2 support (since version 2.5.0). The client automatically detects and uses HTTP/2 when the server supports it, with seamless fallback to HTTP/1.1.

Supported platforms and runtimes Python: all versions included in the build matrix. CPython and PyPy. Ubuntu, Windows, macOS.

Documentation Please refer to the documentation website: https://www.neoteroi.dev/blacksheep/
