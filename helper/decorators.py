# decorators.py
import tornado.web


def all_origin(cls):
    """
    Decorator to add CORS headers to Tornado request handlers.
    """
    original_prepare = getattr(cls, 'prepare', None)
    original_set_default_headers = getattr(cls, 'set_default_headers', None)
    original_options = getattr(cls, 'options', None)

    def prepare(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        if original_prepare:
            original_prepare(self)

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        if original_set_default_headers:
            original_set_default_headers(self)

    def options(self, *args, **kwargs):
        self.set_status(204)
        self.finish()
        if original_options:
            original_options(self, *args, **kwargs)

    cls.prepare = prepare
    cls.set_default_headers = set_default_headers
    cls.options = options
    return cls

