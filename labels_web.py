#!/usr/bin/env python3
import glob
import logging
import logging.config
from itertools import chain

import yamlconf
from wikilabels.wsgi import server

config_paths = sorted(glob.glob("config/*.yaml"))
if __name__ == '__main__':
    config_paths += sorted(glob.glob("config/localhost/*.yaml"))

config = yamlconf.load(*(open(p) for p in config_paths))
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
    application.run(host="0.0.0.0", port=8080, debug=True)
