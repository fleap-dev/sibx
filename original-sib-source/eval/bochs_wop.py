import os
import json
import subprocess

from subprocess import DEVNULL
from bochs import BochsManager


class BochsWOPManager(BochsManager):
    def config(self):
        my_env = os.environ.copy()
        my_env['SOURCE_DATE_EPOCH'] = '1'

        subprocess.run([
            './configure', f'CXX={self.compiler_pp}', f'CC={self.compiler}',
            'CXXFLAGS=-Wno-builtin-macro-redefined -D__LINE__',
            'CFLAGS=-Wno-builtin-macro-redefined -D__LINE__',
        ] + self.variant,
            check=True,
            env=my_env,
            cwd='bochs',
            stdout=DEVNULL)

    # in this case we don't want to use multipatchcheck but implement a alternative approach
    def multipatchcheck(self, *args, **kwargs):
        object_hashes = self.get_hashes()
        with open('/tmp/tmphash', 'w') as file:
            json.dump(object_hashes, file)


MANAGER = BochsWOPManager
