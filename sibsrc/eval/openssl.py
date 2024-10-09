import os
import random
import logging
import subprocess

from projectmanager import ProjectManager
from subprocess import DEVNULL


class OpenSSLManager(ProjectManager):

    OPENSSL_OPTIONS = [
        '-no-dtls',
        '-no-async',
        '-no-dh',
        '-no-secure-memory',
        '-no-dsa',
        '-no-ui-console',
        '-no-rmd160',
        '-no-ts',
        '-no-dgram',
        '-no-cmp',
        '-no-module',
        '-no-ssl-trace',
        '-no-chacha',
        '-no-asm',
        '-no-pic',
        '-no-whirlpool',
        '-no-blake2',
        '-no-aria',
        '-no-poly1305',
        '-no-des',
        '-no-ec2m',
        '-no-camellia',
        '-no-uplink',
        '-no-sm4',
        '-no-threads',
        '-no-scrypt',
        '-no-idea',
        '-no-comp',
        '-no-tls',
        '-no-rc4',
        '-no-fips-securitychecks',
        '-no-sse2',
        '-no-ocb',
        '-no-siv',
        '-no-mdc2',
        '-no-acvp-tests',
        '-no-posix-io',
        '-no-bf',
        '-no-pinshared',
        '-no-deprecated',
        '-no-sock',
        '-no-autoerrinit',
        '-no-capieng',
        '-no-afalgeng',
        '-no-dso',
        '-no-srtp',
        '-no-ssl',
        '-no-loadereng',
        '-no-err',
        '-no-dynamic-engine',
        '-no-tests',
        '-no-autoload-config',
        '-no-rfc3779',
        '-no-ec',
        '-no-md4',
        '-no-multiblock',
        '-no-siphash',
        '-no-stdio',
        '-no-psk',
        '-no-seed',
        '-no-ecdh',
        '-no-rc2',
        '-no-sm2',
        '-no-engine',
        '-no-bulk',
        '-no-makedepend',
        '-no-cms',
        '-no-filenames',
        '-no-nextprotoneg',
        '-no-padlockeng',
        '-no-cached-fetch',
        '-no-srp',
        '-no-legacy',
        '-no-gost',
        '-no-ct',
        '-no-static-engine',
        '-no-sm3',
        '-no-rdrand',
        '-no-ecdsa',
        '-no-ocsp',
        '-no-cast',
        '-no-cmac',
        '-no-autoalginit',
    ]

    ALARM_LIST = [
        'apps/progs.pl',
        'include/crypto/bn_conf.h.in',
        'include/crypto/dso_conf.h.in',
        'include/openssl/asn1.h.in',
        'include/openssl/asn1t.h.in',
        'include/openssl/bio.h.in',
        'include/openssl/cmp.h.in',
        'include/openssl/cms.h.in',
        'include/openssl/conf.h.in',
        'include/openssl/configuration.h.in',
        'include/openssl/crmf.h.in',
        'include/openssl/crypto.h.in',
        'include/openssl/ct.h.in',
        'include/openssl/err.h.in',
        'include/openssl/ess.h.in',
        'include/openssl/fipskey.h.in',
        'include/openssl/lhash.h.in',
        'include/openssl/ocsp.h.in',
        'include/openssl/opensslv.h.in',
        'include/openssl/pkcs12.h.in',
        'include/openssl/pkcs7.h.in',
        'include/openssl/safestack.h.in',
        'include/openssl/srp.h.in',
        'include/openssl/ssl.h.in',
        'include/openssl/ui.h.in',
        'include/openssl/x509.h.in',
        'include/openssl/x509_vfy.h.in',
        'include/openssl/x509v3.h.in',
        'providers/common/der/der_digests_gen.c.in',
        'providers/common/der/der_dsa_gen.c.in',
        'providers/common/der/der_ec_gen.c.in',
        'providers/common/der/der_ecx_gen.c.in',
        'providers/common/der/der_rsa_gen.c.in',
        'providers/common/der/der_sm2_gen.c.in',
        'providers/common/der/der_wrap_gen.c.in',
        'providers/common/include/prov/der_digests.h.in',
        'providers/common/include/prov/der_dsa.h.in',
        'providers/common/include/prov/der_ec.h.in',
        'providers/common/include/prov/der_ecx.h.in',
        'providers/common/include/prov/der_rsa.h.in',
        'providers/common/include/prov/der_sm2.h.in',
        'providers/common/include/prov/der_wrap.h.in',
        'util/mkbuildinf.pl',
    ]

    def config(self):
        my_env = os.environ.copy()
        my_env['SOURCE_DATE_EPOCH'] = '1'

        self.__fix_config()
        argv = [
            './config', f'CC={self.compiler}',
            f'CFLAGS=-fplugin={self.plugin} -Wno-builtin-macro-redefined -D__LINE__', 'no-shared'
        ] + self.variant
        logging.debug(argv)
        subprocess.run(argv, env=my_env, check=True, stdout=DEVNULL)
        self.__restore_config_fixes()

    def build(self):
        rerun = False
        my_env = os.environ.copy()
        my_env['SOURCE_DATE_EPOCH'] = '1'

        try:
            return subprocess.run(['make', '-j' + self.jobs],
                           env=my_env,
                           check=True,
                           text=True,
                           capture_output=True)
        except subprocess.CalledProcessError as e:
            if 'Please run the same make command again' in e.stdout + e.stderr:
                return subprocess.run(['make', '-j' + self.jobs],
                           env=my_env,
                           check=True,
                           text=True,
                           capture_output=True)
            else:
                raise e

    def clean(self):
        subprocess.run(['git', 'clean', '-dfx'],
                       check=True,
                       stdout=DEVNULL,
                       stderr=DEVNULL)

    def post_run(self):
        self.clean()
        self.config()

    def get_random_variant(self):
        flag_count = random.randint(0, len(OpenSSLManager.OPENSSL_OPTIONS) // 2)
        return random.sample(OpenSSLManager.OPENSSL_OPTIONS, flag_count)

    def compile_commands(self, stdin):
        subprocess.run(['compiledb', '--parse', '-'],
                       input=stdin,
                       check=True,
                       stdout=DEVNULL,
                       stderr=DEVNULL)

    def __fix_config(self):
        # add # in front of each line
        subprocess.run([
            'sed',
            '-i',
            r's/^/#/',
            'VERSION.dat'
        ],
            check=True)

        with open("VERSION.dat", "a") as f:
            f.write('MAJOR=3\n')
            f.write('MINOR=3\n')
            f.write('PATCH=3\n')
            f.write('PRE_RELEASE_TAG=beta3-dev\n')
            f.write('BUILD_METADATA=\n')
            f.write('RELEASE_DATE=""\n')
            f.write('SHLIB_VERSION=3\n')

    def __restore_config_fixes(self):
        # remove everything starting at line 8
        subprocess.run([
            'sed',
            '-i',
            r'8,$ d',
            'VERSION.dat'
        ],
            check=True)

        # remove # in front of each line
        subprocess.run([
            'sed',
            '-i',
            r's/^.//',
            'VERSION.dat'
        ],
            check=True)


MANAGER = OpenSSLManager
