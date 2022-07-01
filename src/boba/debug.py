from boba.parser import Parser

if __name__ == '__main__':
    script = '/projects/bdata/kenqgu/Research/MultiverseProject/boba_tea/boba/example/hurricane_copy/template.R'
    out = '/projects/bdata/kenqgu/Research/MultiverseProject/boba_tea/boba/example/hurricane_copy'
    ps = Parser(script, out, None)
    ps.main()