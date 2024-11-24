import os
import subprocess

from subprocess import DEVNULL
from eval import ProjectManager


class LinuxManager(ProjectManager):

    LINUX_CONFIGS = [
        'tinyconfig',
        'defconfig',
        # 'randconfig',
    ]

    ALARM_LIST = [
        'arch/x86/entry/vdso/vdso2c.c',
        'arch/x86/entry/vdso/vdso2c.h',

        'kernel/bounds.s',

        'arch/x86/lib/x86-opcode-map.txt',
        'arch/x86/tools/gen-insn-attr-x86.awk',

        'include/asm-generic/early_ioremap.h',
        'include/asm-generic/irq_regs.h',
        'include/asm-generic/kmap_size.h',
        'include/asm-generic/local64.h',
        'include/asm-generic/mmiowb.h',
        'include/asm-generic/platform-feature.h',
        'include/asm-generic/rwonce.h',
        'include/asm-generic/syscalls_32.h',
        'include/asm-generic/unaligned.h',
        'include/uapi/asm-generic/bpf_perf_event.h',
        'include/uapi/asm-generic/errno.h',
        'include/uapi/asm-generic/fcntl.h',
        'include/uapi/asm-generic/ioctl.h',
        'include/uapi/asm-generic/ioctls.h',
        'include/uapi/asm-generic/ipcbuf.h',
        'include/uapi/asm-generic/param.h',
        'include/uapi/asm-generic/poll.h',
        'include/uapi/asm-generic/resource.h',
        'include/uapi/asm-generic/socket.h',
        'include/uapi/asm-generic/sockios.h',
        'include/uapi/asm-generic/termbits.h',
        'include/uapi/asm-generic/termios.h',
        'include/uapi/asm-generic/types.h',
        'include/uapi/asm-generic/unistd_32.h',
    ]

    def __fix_build(self):
        subprocess.run([
            'sed',
            '-i',
            r's|buf_printf(b, "BUILD_LTO_INFO;\\n");|//buf_printf(b, "BUILD_LTO_INFO;\\n");|',
            'scripts/mod/modpost.c',
        ],
            check=True)

        subprocess.run([
            'sed',
            '-i',
            r's|BUILD_LTO_INFO;|//BUILD_LTO_INFO;|',
            'init/version.c',
        ],
            check=True)

    def __discard_staged_changes(self):
        subprocess.run([
            'sed',
            '-i',
            r's|//BUILD_LTO_INFO;|BUILD_LTO_INFO;|',
            'init/version.c',
        ],
            check=True)

        subprocess.run([
            'sed',
            '-i',
            r's|//buf_printf(b, "BUILD_LTO_INFO;\\n");|buf_printf(b, "BUILD_LTO_INFO;\\n");|',
            'scripts/mod/modpost.c',
        ],
            check=True)

    def config(self):
        pass

    def build(self):
        self.__fix_build()
        subprocess.run([
            'make', '-j' + self.jobs, f'CC={self.compiler}',
            f'KCFLAGS=-fplugin={self.plugin} -Wno-builtin-macro-redefined -D__LINE__',
            'KERNELRELEASE="testing"', 'KBUILD_BUILD_TIMESTAMP=@0', 'KBUILD_BUILD_VERSION=0',
            f'KCONFIG_CONFIG=/config/{self.variant}',
            'vmlinux'
        ],
            check=True,
            stdout=DEVNULL,
            stderr=DEVNULL)

        self.__discard_staged_changes()

    def get_ignore_patterns(self):
        files = [
            'tools/',
            'scripts/',
        ]

        return set(map(lambda f: os.path.join(self.path, f), files))

    def compile_commands(self, _):
        subprocess.run(['scripts/clang-tools/gen_compile_commands.py'],
                       check=True,
                       stdout=DEVNULL,
                       stderr=DEVNULL)

    def get_random_variants(self, count):
        configs = []
        for i in range(0, count):
            if i < len(LinuxManager.LINUX_CONFIGS):
                configs += [LinuxManager.LINUX_CONFIGS[i]]
            else:
                configs += [f'randconfig_{i}']

        return configs


MANAGER = LinuxManager
