#!/usr/bin/env python3

import os
import sys
import time
import random
import logging
import argparse
import subprocess

from subprocess import DEVNULL
from projectmanager import ProjectManager


class Git:

    def __init__(self, path):
        self.path = path

    def checkout(self, commit):
        logging.debug('git checkout %s', commit)
        subprocess.run(['git', 'checkout', '--force', commit],
                       cwd=self.path,
                       check=True,
                       stdout=DEVNULL,
                       stderr=DEVNULL)

    def apply(self, commit):
        logging.debug('Applying %s', commit)
        subprocess.run(['git', 'cherry-pick', '--no-commit', commit, '-m1'],
                       cwd=self.path,
                       check=True,
                       stdout=DEVNULL,
                       stderr=DEVNULL)
        subprocess.run(['git', 'reset'],
                       cwd=self.path,
                       check=True,
                       stdout=DEVNULL)

    def list(self, commits):
        p = subprocess.run(
            ['git', 'rev-list', commits, '--first-parent'],
            check=True,
            cwd=self.path,
            text=True,
            capture_output=True,
        )

        return list(reversed(p.stdout.split('\n')[:-1]))

    def clean(self):
        logging.debug('git clean -dfx')
        subprocess.run(['git', 'clean', '-dxf'],
                       cwd=self.path,
                       check=True,
                       stdout=DEVNULL)

    def reset(self):
        logging.debug('git reset --hard')
        subprocess.run(['git', 'reset', '--hard'],
                       cwd=self.path,
                       check=True,
                       stdout=DEVNULL)


class ReadableDir(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        prospective_dir = values
        if not os.path.isdir(prospective_dir):
            raise argparse.ArgumentTypeError(
                f"readable_dir:{prospective_dir} is not a valid path")
        if os.access(prospective_dir, os.R_OK):
            setattr(namespace, self.dest, prospective_dir)
        else:
            raise argparse.ArgumentTypeError(
                f"readable_dir:{prospective_dir} is not a readable dir")


def run(git, commits, project, clean, skip_initial_clean, num_variants):
    commits = git.list(commits)
    num_commits = len(commits)

    variants = project.get_random_variants(num_variants)

    if project.dump_dir:
        os.makedirs(os.path.join(project.dump_dir, 'info'), exist_ok=True)

    logging.info('Setting up repository...')
    os.chdir(git.path)

    results = [['Index', 'Commit', 'Variant', 'config_t'] + project.header()]
    git.reset()

    var_table = {}

    for i, base_commit in enumerate(commits):
        if i + 1 == num_commits:
            break

        change_commit = commits[i + 1]

        logging.info("[%d/%d] %s", i + 1, num_commits - 1, change_commit)
        git.checkout(base_commit)

        for variant_idx in range(0, num_variants):
            config = variants[variant_idx]
            project.variant = config
            variant_id = project.get_variant_id()
            var_table[variant_id] = config

            logging.debug("Setting variant %d: %s", variant_idx, " ".join(config))

            if i == 0 or clean:
                if not skip_initial_clean:
                    git.reset()
                    git.clean()

                start = time.monotonic()
                project.config()
                end = time.monotonic()
            else:
                start = 0
                end = 0

            results += [
                [i, change_commit, variant_id, end - start] +
                project.run(git, base_commit, change_commit, variant_idx)
            ]

    print(var_table)

    return results


def format_result(commit, sep=',', end='\n'):

    def format_inner(element):
        if isinstance(element, float):
            return f'{element:.3f}'
        if isinstance(element, str):
            return element
        return str(element)

    return sep.join(map(format_inner, commit)) + end


def main():
    parser = argparse.ArgumentParser(description='Evaluation script')
    parser.add_argument('repository', action=ReadableDir)
    parser.add_argument('-c', '--commits', help="start_after...end_including")
    parser.add_argument('-m', '--manager', required=True)
    parser.add_argument('-p', '--plugin')
    parser.add_argument('-t', '--tool')
    parser.add_argument('--compiler')
    parser.add_argument('--clean', action='store_true')
    parser.add_argument('--skip-initial-clean', action='store_true')
    parser.add_argument('-o',
                        '--output',
                        type=argparse.FileType('w'),
                        default=sys.stdout)

    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('--dump-dir')
    parser.add_argument('--num-variants', type=int, default=1)
    parser.add_argument('--seed', type=int, default=0)
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    random.seed(args.seed)

    if args.num_variants > 1:
        args.clean = True

    git = Git(args.repository)
    project_manger = ProjectManager.load(args.manager)(args.repository,
                                                       args.plugin, args.tool, args.compiler,
                                                       args.dump_dir)

    results = run(git, args.commits, project_manger, args.clean,
                  args.skip_initial_clean, args.num_variants)

    args.output.writelines(map(format_result, results))


if __name__ == "__main__":
    main()
