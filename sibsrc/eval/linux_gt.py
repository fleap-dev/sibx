import subprocess

from linux import LinuxManager
from subprocess import DEVNULL


class LinuxGroundTruthManager(LinuxManager):

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

    def run(self, *args):
        return self.generate_ground_truth(*args)


MANAGER = LinuxGroundTruthManager
