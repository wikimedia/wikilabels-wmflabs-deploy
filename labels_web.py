#!/usr/bin/env python3
import glob
import logging

import yamlconf
from wikilabels.wsgi import server

config = yamlconf.load(*(open(p) for p in sorted(glob.glob("config/*.yaml"))))

application = server.configure(config)


if __name__ == '__main__':
    logging.getLogger('wikilabels').setLevel(logging.DEBUG)

    application.debug = True
    application.run(host="0.0.0.0", debug=True)
