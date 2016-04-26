#!/usr/bin/env python3
import glob
import logging
import logging.config

import yamlconf
from wikilabels.wsgi import server

config = yamlconf.load(*(open(p) for p in sorted(glob.glob("config/*.yaml"))))

application = server.configure(config)

with open("logging_config.yaml") as f:
    logging_config = yamlconf.load(f)
    logging.config.dictConfig(logging_config)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(name)s -- %(message)s'
)

if __name__ == '__main__':
    logging.getLogger('wikilabels').setLevel(logging.DEBUG)

    application.debug = True
    application.run(host="0.0.0.0", debug=True)
