"""

"""

import bottle
import os
import sys

# routes contains the HTTP handlers for our server
import routes


if '--debug' in sys.argv[1:]:
    #if --debug is used in the arguments we can run the server in debug mode.
    bottle.debug(True)

if __name__ == '__main__':

    server_root = os.path.abspath(os.path.dirname(__file__))
    static_root = os.path.join(server_root, 'static').replace('\\', '/')
    host = os.environ.get('SERVER_HOST', 'localhost')
    try:
        port = int(os.environ.get('SERVER_PORT', '8080'))
    except ValueError:
        port = 8080

    @bottle.route('/static/<filepath:path>')
    def server_static(filepath):
        #the server need to serve the static files
        return bottle.static_file(filepath, root=static_root)

    # start server
    bottle.run(server='wsgiref', host=host, port=port)
