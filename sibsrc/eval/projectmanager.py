import os
import sys
import json
import time
import shutil
import hashlib
import logging
import subprocess
import importlib.util

from subprocess import DEVNULL


class ProjectManager:

    ALARM_LIST = None

    def __init__(self, path, plugin, tool, compiler, dump_dir):
        self.path = path
        self.plugin = plugin
        self.jobs = str(os.cpu_count())
        self.tool = tool
        self.compiler = compiler
        if compiler:
            self.compiler_pp = compiler.replace('clang', 'clang++')
        self.dump_dir = dump_dir
        self.variant = ""

    @staticmethod
    def load(path):
        module_name = "manager"

        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        return module.MANAGER

    def get_variant_id(self):
        return hashlib.blake2b(" ".join(self.variant).encode('utf-8')).hexdigest()[:8]

    def __get_current_compiledbs(self, change_commit):
        ret = []
        for root, _, files in os.walk(self.dump_dir):
            for file in files:
                if not file.endswith('-compile_commands.json'):
                    continue

                commit, variant, _ = file.split('-')
                if not commit == change_commit:
                    continue

                ret += [f'{variant}:{os.path.join(root, file)}']
        return ret

    def multipatchcheck(self, commit, variant_aware=False, check=False, change_commit=None):
        info_dir = os.path.join(self.dump_dir, 'info')

        argv = [self.tool, 'analyze', '--filter-asm', self.path]
        if variant_aware:
            var_id = self.get_variant_id()
            argv += ['--commit', commit, '--variant', var_id, '--storage', info_dir, '--compile-commands', '--dump-only']

        if check:
            argv += ['--commit', commit, '--storage', info_dir, '--check-storage']
            argv += ['--compile-commands-path-map'] + self.__get_current_compiledbs(change_commit)
            if self.ALARM_LIST:
                argv += ['--compare-git'] + self.ALARM_LIST

        if logging.root.level < logging.DEBUG:
            p = subprocess.run(argv,
                               check=False,
                               stdout=DEVNULL,
                               stderr=DEVNULL)
        else:
            logging.debug(argv)
            p = subprocess.run(argv,
                               check=False,
                               text=True,
                               capture_output=True)
            logging.debug(p.stdout)
            logging.debug(p.stderr)
        return p

    @staticmethod
    def __hash_file(path: str):
        with open(path, 'rb') as f:
            return hashlib.blake2b(f.read()).hexdigest()

    def get_ignore_patterns(self):
        return []

    def get_hashes(self):
        ignore_patterns = self.get_ignore_patterns()

        def matches_ignored(s):
            for p in ignore_patterns:
                if s.startswith(p):
                    return True
            return False

        object_hashes = {}
        for root, _, files in os.walk(self.path):
            object_hashes.update(
                map(
                    lambda f: (f, ProjectManager.__hash_file(f)),
                    filter(
                        lambda f: not matches_ignored(f),
                        map(
                            lambda f: os.path.join(root, f),
                            filter(
                                lambda f: f.endswith('.o') and not f.endswith(
                                    '.mod.o'), files)))))

        return object_hashes

    def config(self):
        raise NotImplementedError()

    def build(self):
        raise NotImplementedError()

    def clean(self):
        subprocess.run(['make', 'clean'],
                       check=True,
                       stdout=DEVNULL,
                       stderr=DEVNULL)

    def post_run(self):
        pass

    def get_random_variant(self):
        raise NotImplementedError()

    def get_random_variants(self, count):
        # be careful when modifying because the set of configs may be affected
        vars = [[]]
        for i in range(1, count):
            vars.append(self.get_random_variant())

        var_set = set(map(tuple, vars))
        if len(var_set) == count:
            return vars

        var_set.remove(tuple([]))
        while len(var_set) < count - 1:
            var_set.add(tuple(self.get_random_variant()))

        return [[]] + list(sorted(map(list, var_set)))

    def __diff_objects(base_objects, change_objects):
        equal = True
        for file, base_hash in base_objects.items():
            new_hash = change_objects.get(file)
            if not new_hash:
                equal = False
                logging.debug('file removed: %s', file)
            elif base_hash != new_hash:
                equal = False
                logging.debug('file changed: %s', file)

        new_files = base_objects.keys() - change_objects.keys()
        if new_files:
            logging.debug('files added: %s', new_files)
            equal = False

        return equal

    def __get_untracked_compiler_input(self, path):
        with open(path, 'r') as f:
            uses = json.load(f)

        compiled_files = set(uses['used_lines'].keys())

        p = subprocess.run(['git', 'ls-files'], check=True, text=True, capture_output=True)

        tracked_files = p.stdout.splitlines()
        tracked_files = set(map(lambda f: os.path.join(self.path, f), tracked_files))

        return sorted(compiled_files - tracked_files)

    def header(self):
        return ['build_t', 'predict_t', 'untracked']

    def header_ggt(self):
        return ['build_t']

    def header_check(self):
        return ['check_t', 'affected', 'gt_equal', 'gt_changed', 'gt_build_fail', 'notes']

    def header_check_wop(self):
        return ['check_t', 'equal', 'changed', 'build_fail', 'notes']

    def generate_ground_truth(self, git, base_commit, change_commit, variant_idx):
        results = []

        try:
            start = time.monotonic()
            self.build()
            end = time.monotonic()
        except Exception as e:
            logging.error(e)
            return [f'build of {base_commit} failed']
        results += [end - start]

        return results

    def run_check_per_variant(self, git, base_commit, change_commit, variant_idx):
        results = []

        # apply changes
        git.apply(change_commit)

        # check for problematic changes
        git_diff = subprocess.run(['git', 'diff', '--stat'],
                                  check=True,
                                  text=True,
                                  capture_output=True)

        notes = []
        if 'Makefile' in git_diff.stdout:
            notes += ['Makefile']

        if 'configure' in git_diff.stdout:
            notes += ['Configure']

        if 'tools/' in git_diff.stdout or 'tool/' in git_diff.stdout:
            notes += ['tools']

        if '.s' in git_diff.stdout.lower() or '.asm' in git_diff.stdout.lower():
            notes += ['asm']

        variant = self.get_variant_id()
        fail_variant = ""

        start = time.monotonic()
        base_path = os.path.join(self.dump_dir, f'{base_commit}-{self.get_variant_id()}-hashes.json')
        change_path = os.path.join(self.dump_dir, f'{change_commit}-{self.get_variant_id()}-hashes.json')

        if os.path.exists(base_path) and os.path.exists(change_path):
            with open(base_path, 'r') as f:
                base_objects = json.load(f)
            with open(change_path, 'r') as f:
                change_objects = json.load(f)
            equal = ProjectManager.__diff_objects(base_objects, change_objects)
            end = time.monotonic()
            results += [end - start]
        else:
            results += [0]
            fail_variant = variant
            print(f'failed {base_commit} {variant}')

        equal_variant = variant if not fail_variant and equal else ""
        changed_variant = variant if not fail_variant and not equal else ""

        results += [equal_variant]
        results += [changed_variant]
        results += [fail_variant]

        results += [('|').join(notes)]

        return results

    def run_check(self, git, base_commit, change_commit, variant_idx):
        results = []

        # apply changes
        git.apply(change_commit)

        # check for problematic changes
        git_diff = subprocess.run(['git', 'diff', '--stat'],
                                  check=True,
                                  text=True,
                                  capture_output=True)

        notes = []
        if 'Makefile' in git_diff.stdout:
            notes += ['Makefile']

        if 'configure' in git_diff.stdout:
            notes += ['Configure']

        if 'tools/' in git_diff.stdout or 'tool/' in git_diff.stdout:
            notes += ['tools']

        if '.s' in git_diff.stdout.lower() or '.asm' in git_diff.stdout.lower():
            notes += ['asm']

        start = time.monotonic()
        p = self.multipatchcheck(base_commit, check=True, change_commit=change_commit)
        end = time.monotonic()
        results += [end - start]

        affected_variants = []
        for line in p.stdout.split('\n'):
            logging.debug(line)
            if 'affected' in line:
                affected_variants = line.split('[mpc] ', 1)[1].removesuffix(' affected')
                affected_variants = list(set(eval(affected_variants)))  # remove duplicates
                affected_variants.sort()
                break

        results += ["|".join(affected_variants)]

        # validation
        base_variants = self.__get_objects_by_variant(base_commit)
        change_variants = self.__get_objects_by_variant(change_commit)

        equal_variants = []
        changed_variants = []
        fail_variants = []

        if not base_variants:
            return [f'build of {base_commit} failed']

        for variant, base_objects in base_variants.items():
            if variant not in change_variants:
                fail_variants.append(variant)
            elif ProjectManager.__diff_objects(base_objects, change_variants[variant]):
                equal_variants.append(variant)
            else:
                changed_variants.append(variant)

        equal_variants.sort()
        changed_variants.sort()
        fail_variants.sort()

        results += ["|".join(equal_variants)]
        results += ["|".join(changed_variants)]
        results += ["|".join(fail_variants)]

        results += [('|').join(notes)]

        return results

    def __get_objects_by_variant(self, commit):
        entries = filter(lambda f: f.endswith('-hashes.json'), os.listdir(self.dump_dir))
        entries = filter(lambda f: f.startswith(commit), entries)
        entries = map(lambda f: os.path.join(self.dump_dir, f), entries)

        objects_by_variant = {}
        for entry in entries:
            _, variant, _ = entry.split('-')
            with open(entry, 'r') as f:
                objects_by_variant[variant] = json.load(f)

        return objects_by_variant

    def run(self, git, base_commit, change_commit, variant_idx):
        results = []

        # make -jn
        try:
            start = time.monotonic()
            p = self.build()
            end = time.monotonic()
        except Exception as e:
            logging.error(e)
            return [f'build of {base_commit} failed']
        results += [end - start]

        base_objects = self.get_hashes()

        try:
            self.compile_commands(p.stdout.encode() if p else None)
        except Exception as e:
            logging.error(e)
            return [f'compile commands of {base_commit} failed']

        # rebuild required?
        start = time.monotonic()
        p = self.multipatchcheck(base_commit, variant_aware=True)
        end = time.monotonic()
        results += [end - start]
        if p:
            logging.debug('RESULT: %d', p.returncode)
            assert p.returncode == 0, p.stderr

        variant_id = self.get_variant_id()

        path = os.path.join(self.dump_dir, f'info/{base_commit}-{variant_id}.json')
        if os.path.exists(path):
            # only relevant when using mvpc
            results += [f'"{self.__get_untracked_compiler_input(path)}"']
        else:
            results += []

        path = os.path.join(self.dump_dir, f'{base_commit}-{variant_id}-compile_commands.json')
        shutil.copy2('compile_commands.json', path)

        # store hashes of object files
        path = os.path.join(self.dump_dir, f'{base_commit}-{variant_id}-hashes.json')
        if not os.path.exists(path):
            with open(path, 'w') as file:
                json.dump(base_objects, file, sort_keys=True)

        # try:
        #     self.post_run()
        # except Exception as e:
        #     logging.error(e)
        #     notes += ['post_run']
        #     git.clean()
        #     self.config()

        return results
