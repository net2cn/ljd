#!/usr/bin/python3
#
# The MIT License (MIT)
#
# Copyright (c) 2013 Andrian Nord
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import os, sys
import codecs
import argparse

import ljd.rawdump.parser
import ljd.pseudoasm.writer
import ljd.ast.builder
import ljd.ast.validator
import ljd.ast.locals
import ljd.ast.slotworks
import ljd.ast.unwarper
import ljd.ast.mutator
import ljd.lua.writer

def load_file_from_dir(dir_path):
    ret = []
    for file in os.listdir(dir_path):
        path_comb = os.path.join(dir_path, file)
        if os.path.isdir(path_comb):
            ret += load_file_from_dir(path_comb)
        else:
            ret.append(path_comb)
    return ret


def dump(name, obj, level=0):
    indent = level * '\t'

    if name is not None:
        prefix = indent + name + " = "
    else:
        prefix = indent

    if isinstance(obj, (int, float, str)):
        print(prefix + str(obj))
    elif isinstance(obj, list):
        print(prefix + "[")

        for value in obj:
            dump(None, value, level + 1)

        print(indent + "]")
    elif isinstance(obj, dict):
        print(prefix + "{")

        for key, value in obj.items():
            dump(key, value, level + 1)

        print(indent + "}")
    else:
        print(prefix + obj.__class__.__name__)

        for key in dir(obj):
            if key.startswith("__"):
                continue

            val = getattr(obj, key)
            dump(key, val, level + 1)

def do_decompile(file_in):
    header, prototype = ljd.rawdump.parser.parse(file_in)

    if not prototype:
        return 1

    # TODO: args
    # ljd.pseudoasm.writer.write(sys.stdout, header, prototype)

    ast = ljd.ast.builder.build(prototype)

    assert ast is not None

    ljd.ast.validator.validate(ast, warped=True)

    ljd.ast.mutator.pre_pass(ast)

    # ljd.ast.validator.validate(ast, warped=True)

    ljd.ast.locals.mark_locals(ast)

    # ljd.ast.validator.validate(ast, warped=True)

    ljd.ast.slotworks.eliminate_temporary(ast)

    # ljd.ast.validator.validate(ast, warped=True)

    if True:
        ljd.ast.unwarper.unwarp(ast)

        # ljd.ast.validator.validate(ast, warped=False)

        if True:
            ljd.ast.locals.mark_local_definitions(ast)

            # ljd.ast.validator.validate(ast, warped=False)

            ljd.ast.mutator.primary_pass(ast)

            ljd.ast.validator.validate(ast, warped=False)

    #ljd.lua.writer.write(sys.stdout, ast)
    return ast


def main():
    parser = argparse.ArgumentParser(
        description='LJD-mod: LuaJit raw-bytecode Decompiler modified')
    parser.add_argument('-i', help='Input file/folder.',
                        dest='input', type=str, required=True)
    parser.add_argument('-o', help='Output folder.', dest='output', type=str)

    args = parser.parse_args()

    assert os.path.exists(args.input), 'The input does not exists'

    # prepare variables to store files that throw exceptions during decompliation.
    errorred_files = []

    if os.path.isfile(args.input):
        ast = do_decompile(args.input)
        ljd.lua.writer.write(sys.stdout, ast)
    else:
        if args.output == None and not os.isdir(args.output):
            assert 'Please specify a output directory when input is a directory.'

        if not os.path.exists(args.output):
            os.mkdir(args.output)

        files = load_file_from_dir(args.input)

        for file in files:
            print('Decompiling ' + file)
            basename = os.path.basename(file)
            file_name, file_extension = os.path.splitext(basename)
            # ".bytes" is for files extracted from Unity game engine.
            # You will want to add more extensions since they usually vary from project to project.
            if file_extension not in ['.lua', '.luac', ".bytes"]:
                continue
            
            try:
                ast = do_decompile(file)
            except Exception as e:
                print('%s occurred when decompiling %s' % (type(e).__name__, file))
                errorred_files.append([file,type(e).__name__])
                pass

            with codecs.open(args.output + '\\' + file_name, 'w', 'utf-8') as f:
                ljd.lua.writer.write(f,ast)

        print('================================================================')
        print('Decompilation Done! Error and skipped files are listed as below:')
        print('================================================================')
        for file in errorred_files:
            print(file[0] + ', with Exception of %s' %file[1])

if __name__ == "__main__":
    main()
# vim: ts=8 noexpandtab nosmarttab softtabstop=8 shiftwidth=8
