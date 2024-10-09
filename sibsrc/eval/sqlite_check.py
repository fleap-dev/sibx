from sqlite import SQLiteManager


class SQLiteCheckManager(SQLiteManager):
    def header(self):
        return self.header_check()

    def run(self, *args):
        return self.run_check(*args)

    def config(self):
        pass


MANAGER = SQLiteCheckManager
