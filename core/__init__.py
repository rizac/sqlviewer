def shutdown_server(request):  # http://flask.pocoo.org/snippets/67/
    """Shutdown the flask server. This method is intended to be called from within a view
    :param request: the flask request object (`from flask import request`) usually available
    within a view
    """
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


_cache_address = None


def get_cache_address():
    """Returns the cache address passed via the command line, if any.
    *WARNING*: this method will return a valid address (if any) only the first time is called.
    Afterwrds the cache address is set to None and None will be returned"""
    global _cache_address
    address = _cache_address
    set_chache_address(None)
    return address


def set_chache_address(address):
    """Sets the cahce address. Called from within the main class when a user provides a db url via
    the command line. The page loads and then queries get_cahce_address once"""
    global _cache_address
    _cache_address = address
