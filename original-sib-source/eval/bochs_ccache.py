import os
import subprocess

from subprocess import DEVNULL
from bochs_wop import BochsWOPManager


class BochsCcacheManager(BochsWOPManager):
    pass


MANAGER = BochsCcacheManager
