from linux import LinuxManager


class LinuxWOPCheckManager(LinuxManager):
    def config(self):
        pass

    def header(self):
        return self.header_check_wop()

    def run(self, *args):
        return self.run_check_per_variant(*args)


MANAGER = LinuxWOPCheckManager
