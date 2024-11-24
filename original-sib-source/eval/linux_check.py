from linux import LinuxManager


class LinuxCheckManager(LinuxManager):
    def header(self):
        return self.header_check()

    def run(self, *args):
        return self.run_check(*args)

    def config(self):
        pass


MANAGER = LinuxCheckManager
