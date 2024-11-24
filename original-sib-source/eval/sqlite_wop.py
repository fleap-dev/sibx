import json
import subprocess

from subprocess import DEVNULL
from sqlite import SQLiteManager


class SQLiteWOPManager(SQLiteManager):
    def config(self):
        subprocess.run([
            './configure', f'CC={self.compiler}', '--disable-tcl', '--disable-amalgamation',
            'CFLAGS=-Wno-builtin-macro-redefined -D__LINE__'
        ] + self.variant,
            check=True,
            stdout=DEVNULL)

    # in this case we don't want to use multipatchcheck but implement a alternative approach
    def multipatchcheck(self, *args, **kwargs):
        object_hashes = self.get_hashes()
        with open('/tmp/tmphash', 'w') as file:
            json.dump(object_hashes, file)


MANAGER = SQLiteWOPManager
