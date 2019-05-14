import os.path


class QuickDERgeneric(object):
    def __init__(self, outfn, outext):
        self.unit, curext = os.path.splitext(outfn)
        if curext == '.h':
            raise Exception('File cannot overwrite itself -- use another extension than ' + outext + ' for input files')
        self.outfile = open(self.unit + outext, 'w')

        self.comma1 = None
        self.comma0 = None

    def write(self, txt):
        self.outfile.write(txt)

    def writeln(self, txt=''):
        self.outfile.write(txt + '\n')

    def newcomma(self, comma, firstcomma=''):
        self.comma0 = firstcomma
        self.comma1 = comma

    def comma(self):
        self.write(self.comma0)
        self.comma0 = self.comma1

    def getcomma(self):
        return self.comma1, self.comma0

    def setcomma(self, comma1, comma0):
        self.comma1 = comma1
        self.comma0 = comma0

    def close(self):
        self.outfile.close()