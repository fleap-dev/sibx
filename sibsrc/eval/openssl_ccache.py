import os
import subprocess

from subprocess import DEVNULL
from openssl_wop import OpenSSLWOPManager


class OpenSSLCcacheManager(OpenSSLWOPManager):
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


MANAGER = OpenSSLCcacheManager
