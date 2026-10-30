from urllib.parse import parse_qsl, urlencode


class OriginalPathMiddleware:
    """Restore the public URL after Vercel routes it through /api/index."""

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        query = parse_qsl(environ.get("QUERY_STRING", ""), keep_blank_values=True)
        path_values = [value for key, value in query if key == "__vercel_path"]
        if path_values:
            environ["PATH_INFO"] = "/" + path_values[-1].lstrip("/")
            environ["QUERY_STRING"] = urlencode(
                [(key, value) for key, value in query if key != "__vercel_path"]
            )
        return self.app(environ, start_response)
