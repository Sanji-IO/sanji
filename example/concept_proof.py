#!/usr/bin/env python
# -*- coding: UTF-8 -*-


import dataset

class DictSQL(object):
    def __init__(self, db_file):
        self.db_file = db_file
        self.db = dataset.connect("sqlite:///" + self.db_file)


    def __del__(self):
        #print "__del__()"
        pass

    def print_table(self, table_name):
        for row in self.db[table_name].all():
            print row

    def print_db(self):
        for table in self.db.tables:
            print table
            self.print_table(table)

    def show_tables(self):
        print self.db.tables


    def insert(self):
        pass






if __name__ == '__main__':
    pass
