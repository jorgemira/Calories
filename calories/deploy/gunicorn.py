import multiprocessing
from abc import ABC

from gunicorn.app.base import BaseApplication

from calories.main import cfg


def number_of_workers():
    return (multiprocessing.cpu_count() * 2) + 1


class StandaloneApplication(BaseApplication, ABC):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def run(app):
    options = {
        "bind": "%s:%s" % (cfg.ADDRESS, cfg.PORT),
        "workers": number_of_workers(),
        "keyfile": cfg.KEYFILE,  # 'certs/server.key',
        "certfile": cfg.CERTFILE,  # 'certs/server.crt',
        "ca-certs": cfg.CACERTS,  # 'certs/ca-crt.pem',
        "cert-reqs": 2,
    }

    return StandaloneApplication(app, options).run()
