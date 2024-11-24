import json
import subprocess

from linux import LinuxManager
from subprocess import DEVNULL


class LinuxWOPManager(LinuxManager):

    def build(self):
        self._LinuxManager__fix_build()
        subprocess.run([
            'make', '-j' + self.jobs, f'CC={self.compiler}',
            'KCFLAGS= -Wno-builtin-macro-redefined -D__LINE__',
            'KERNELRELEASE="testing"', 'KBUILD_BUILD_TIMESTAMP=@0', 'KBUILD_BUILD_VERSION=0',
            f'KCONFIG_CONFIG=/config/{self.variant}',
            'vmlinux',
        ],
            check=True,
            stdout=DEVNULL,
            stderr=DEVNULL)

        self._LinuxManager__discard_staged_changes()

    # in this case we don't want to use multipatchcheck but implement a alternative approach
    def multipatchcheck(self, *args, **kwargs):
        object_hashes = self.get_hashes()
        with open('/tmp/tmphash', 'w') as file:
            json.dump(object_hashes, file)


MANAGER = LinuxWOPManager
