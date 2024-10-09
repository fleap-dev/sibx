import os
import random
import logging
import subprocess

from projectmanager import ProjectManager
from subprocess import DEVNULL


class BochsManager(ProjectManager):

    BOCHS_OPTIONS = [
        '--disable-largefile',
        '--enable-idle-hack',
        '--enable-plugins',
        '--disable-a20-pin',
        '--enable-x86-64',
        '--enable-smp',
        '--enable-long-phy-address',
        '--enable-repeat-speedups',
        '--enable-fast-function-calls',
        '--enable-handlers-chaining',
        '--enable-trace-linking',
        '--enable-configurable-msrs',
        '--disable-show-ips',
        # '--enable-cpp',
        '--enable-debugger',
        # '--enable-gdb-stub',
        '--enable-all-optimizations',
        '--enable-readline',
        '--disable-logging',
        '--disable-stats',
        # '--disable-fpu',
        '--enable-vmx=1',
        '--enable-svm',
        '--enable-protection-keys',
        '--enable-cet',
        '--enable-uintr',
        '--enable-3dnow',
        '--enable-memtype',
        '--enable-avx',
        '--enable-evex',
        # '--enable-amx',
        '--enable-x86-debugger',
        '--disable-pci',
        '--enable-pcidev',
        '--enable-usb',
        '--enable-usb-ohci',
        # '--enable-usb-ehci', seems to be broken
        '--enable-usb-xhci',
        '--enable-ne2000',
        '--enable-pnic',
        '--enable-e1000',
        # '--enable-using-libslirp',
        '--enable-raw-serial',
        '--enable-clgd54xx',
        '--enable-voodoo',
        '--disable-cdrom',
        '--enable-sb16',
        '--enable-es1370',
        '--enable-busmouse',
        '--disable-docbook',
        '--disable-xpm',
    ]

    BOCHS_X64_OPTIONS = [
        '--enable-svm',
        '--enable-protection-keys',
        '--enable-cet',
        '--enable-uintr',
        '--enable-avx',
        '--enable-evex',
    ]

    BOCHS_PCI_OPTIONS = [
        '--enable-pcidev',
        '--enable-usb',
        '--enable-usb-ohci',
        '--enable-usb-ehci',
        '--enable-usb-xhci',
        '--enable-es1370',
        '--enable-e1000',
        '--enable-voodoo',
        '--enable-pnic',
    ]

    def config(self):
        my_env = os.environ.copy()
        my_env['SOURCE_DATE_EPOCH'] = '1'

        argv = [
            './configure',
            f'CXX={self.compiler_pp}',
            f'CC={self.compiler}',
            f'CXXFLAGS=-fplugin={self.plugin} -Wno-builtin-macro-redefined -D__LINE__ -D__TIME__="0" -D__DATE__="0" -DNDEBUG',
            f'CFLAGS=-fplugin={self.plugin} -Wno-builtin-macro-redefined -D__LINE__',
        ] + self.variant
        logging.debug(argv)
        subprocess.run(argv, env=my_env, cwd='bochs', check=True, stdout=DEVNULL)
        # subprocess.run(argv, env=my_env, cwd='bochs', check=True)

    def build(self):
        my_env = os.environ.copy()
        my_env['SOURCE_DATE_EPOCH'] = '1'

        p = subprocess.run(['make', '--output-sync','-j' + self.jobs],
                              env=my_env,
                              check=True,
                              text=True,
                              cwd='bochs',
                              capture_output=True)

        # logging.debug(p.stdout)
        # logging.debug(p.stderr)
        return p

    def clean(self):
        subprocess.run(['git', 'clean', '-dfx'],
                       check=True,
                       stdout=DEVNULL,
                       stderr=DEVNULL)

    def post_run(self):
        self.clean()
        self.config()

    def get_random_variant(self):
        flag_count = random.randint(0, len(BochsManager.BOCHS_OPTIONS) // 2)
        flags = random.sample(BochsManager.BOCHS_OPTIONS, flag_count)

        if '--enable-x86-64' not in flags and set(flags) & set(self.BOCHS_X64_OPTIONS):
            flags.append('--enable-x86-64')

        if '--disable-pci' in flags:
            flags = list(filter(lambda flag: flag not in self.BOCHS_PCI_OPTIONS, flags))

        if '--enable-evex' in flags and '--enable-avx' not in flags:
            flags.append('--enable-avx')

        return flags

    def compile_commands(self, stdin):
        subprocess.run(['compiledb', '--parse', '-'],
                       input=stdin,
                       check=True,
                       stdout=DEVNULL,
                       stderr=DEVNULL)


MANAGER = BochsManager
