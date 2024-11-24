import random
import subprocess

from projectmanager import ProjectManager
from subprocess import DEVNULL


class SQLiteManager(ProjectManager):

    SQLITE_OPTIONS = [
        "--disable-largefile",
        "--disable-threadsafe",
        "--disable-readline",
        "--disable-load-extension",
        "--disable-math",
        "--enable-memsys5",
        "--enable-memsys3",
        # "--enable-fts3",
        "--enable-fts4",
        # "--enable-fts5",
        # '--enable-json1',
        "--enable-update-limit",
        "--enable-geopoly",
        "--enable-rtree",
        "--enable-session",
    ]

    ALARM_LIST = [
        'config.h.in',
        # fts5 was not used for the evaluation
        # 'ext/fts5/fts5.h',
        # 'ext/fts5/fts5Int.h',
        # 'ext/fts5/fts5_aux.c',
        # 'ext/fts5/fts5_buffer.c',
        # 'ext/fts5/fts5_config.c',
        # 'ext/fts5/fts5_expr.c',
        # 'ext/fts5/fts5_hash.c',
        # 'ext/fts5/fts5_index.c',
        # 'ext/fts5/fts5_main.c',
        # 'ext/fts5/fts5_storage.c',
        # 'ext/fts5/fts5_tokenize.c',
        # 'ext/fts5/fts5_unicode2.c',
        # 'ext/fts5/fts5_varint.c',
        # 'ext/fts5/fts5_vocab.c',
        # 'ext/fts5/fts5parse.y',
        'src/parse.y',
        'src/sqlite.h.in',
        'src/vdbe.c',
        'src/vdbe.h',
        'tool/mkkeywordhash.c',
    ]

    def config(self):
        subprocess.run([
            # './configure', '--cache-file=/tmp/sqlite.cache', f'CC={self.compiler}', '--disable-tcl', '--disable-amalgamation',
            './configure', f'CC={self.compiler}', '--disable-tcl', '--disable-amalgamation',
            f'CFLAGS=-fplugin={self.plugin} -Wno-builtin-macro-redefined -D__LINE__'
        ] + self.variant,
            check=True,
            stdout=DEVNULL)

    def __fix_build(self):
        subprocess.run([
            'sed',
            '-i',
            r's/set zVersion/set zVersion "0.0.0" ;# set zVersion/',
            'tool/mksqlite3h.tcl',
        ],
            check=True)

        subprocess.run([
            'sed',
            '-i',
            r's/set zSourceId/set zSourceId "0000-00-00 00:00:00 0000000000000000000000000000000000000000000000000000000000000000" ;# set zSourceId/',
            'tool/mksqlite3h.tcl',
        ],
            check=True)

    def __restore_fixes(self):
        subprocess.run([
            'sed',
            '-i',
            r's/set zVersion "0.0.0" ;# //',
            'tool/mksqlite3h.tcl',
        ],
            check=True)

        subprocess.run([
            'sed',
            '-i',
            r's/set zSourceId "0000-00-00 00:00:00 0000000000000000000000000000000000000000000000000000000000000000" ;# //',
            'tool/mksqlite3h.tcl',
        ],
            check=True)

    def build(self):
        self.config()
        self.__fix_build()
        p = subprocess.run(['make', '-j' + self.jobs],
                       check=True,
                       text=True,
                       capture_output=True)
        self.__restore_fixes()
        return p

    def get_random_variant(self):
        flag_count = random.randint(0, len(SQLiteManager.SQLITE_OPTIONS) / 2)
        return random.sample(SQLiteManager.SQLITE_OPTIONS, flag_count)

    def compile_commands(self, stdin):
        subprocess.run(['compiledb', '--parse', '-'],
                       input=stdin,
                       check=True,
                       stdout=DEVNULL,
                       stderr=DEVNULL)


MANAGER = SQLiteManager
