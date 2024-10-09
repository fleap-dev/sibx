import subprocess

from subprocess import DEVNULL
from sqlite import SQLiteManager


class SQLiteGroundTruthManager(SQLiteManager):
    def config(self):
        subprocess.run([
            './configure', f'CC={self.compiler}', '--disable-tcl', '--disable-amalgamation',
            'CFLAGS=-Wno-builtin-macro-redefined -D__LINE__'
        ] + self.variant,
            check=True,
            stdout=DEVNULL)

    def run(self, *args):
        return self.generate_ground_truth(*args)


MANAGER = SQLiteGroundTruthManager
