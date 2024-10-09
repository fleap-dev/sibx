import subprocess

from subprocess import DEVNULL
from sqlite_wop import SQLiteWOPManager


class SQLiteCcacheManager(SQLiteWOPManager):
    def config(self):
        subprocess.run([
            './configure', f'CC={self.compiler}', '--disable-tcl', '--disable-amalgamation',
            'CFLAGS=-Wno-builtin-macro-redefined -D__LINE__'
        ] + self.variant,
            check=True,
            stdout=DEVNULL)


MANAGER = SQLiteCcacheManager
