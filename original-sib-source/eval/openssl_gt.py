
import subprocess

from subprocess import DEVNULL
from openssl import OpenSSLManager


class OpenSSLGroundTruthManager(OpenSSLManager):
    def config(self):
        subprocess.run([
            './config', f'CC={self.compiler}',
            'CFLAGS=-Wno-builtin-macro-redefined -D__LINE__', 'no-shared'
        ] + self.variant,
            check=True,
            stdout=DEVNULL)

    def run(self, *args):
        return self.generate_ground_truth(*args)


MANAGER = OpenSSLGroundTruthManager
