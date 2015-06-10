#!/usr/bin/env python3
import os

from flask import request

import yamlconf
from wikilabels.wsgi import server

config = yamlconf.load(open("labels.wmflabs.org.yaml"))

application = server.configure(config)
application.debug = True


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug = True)
