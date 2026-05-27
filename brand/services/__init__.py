"""Business rules.

Views in this project are thin: they parse the request, call one function in
here, and render. Everything that decides *what happens* lives in this package
so it can be unit-tested without an HTTP client.
"""
