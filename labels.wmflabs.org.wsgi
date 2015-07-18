#!/usr/bin/env python3
import os

from flask import request
from wikilabels.wsgi import server

import yamlconf

config = yamlconf.load(open("labels.wmflabs.org.yaml"))
# FIXME: DON'T DO THIS
db_config = config['database']['config']
config['database'] = yamlconf.load(open(db_config))

application = server.configure(config)
application.debug = True

if __name__ == '__main__':
    application.run(host="0.0.0.0", debug = True)
