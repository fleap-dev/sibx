import os
import json
import subprocess

from subprocess import DEVNULL
from openssl import OpenSSLManager


class OpenSSLWOPManager(OpenSSLManager):
    def config(self):
        my_env = os.environ.copy()
        my_env['SOURCE_DATE_EPOCH'] = '1'

        self._OpenSSLManager__fix_config()
        subprocess.run([
            './config', f'CC={self.compiler}',
            'CFLAGS=-Wno-builtin-macro-redefined -D__LINE__', 'no-shared'
        ] + self.variant,
            check=True,
            stdout=DEVNULL)
        self._OpenSSLManager__restore_config_fixes()

    # in this case we don't want to use multipatchcheck but implement a alternative approach
    def multipatchcheck(self, *args, **kwargs):
        object_hashes = self.get_hashes()
        with open('/tmp/tmphash', 'w') as file:
            json.dump(object_hashes, file)


MANAGER = OpenSSLWOPManager
