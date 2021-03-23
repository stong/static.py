#!/usr/bin/env python3

import re
import os
import sys
import glob
import stat
import shutil
import subprocess

regexp = re.compile(r'(.+ => )?(.+) \(0x[0-9a-f]{16}\)')
ldd = shutil.which('ldd')
assert ldd

def visit(binary, outdir, visited, level=0):
    if binary in visited:
        return
    visited.add(binary)

    indent = '    '*level
    filename = os.path.basename(binary)
    dst = os.path.join(outdir, filename)
    assert not dst.startswith('/')
    if not os.path.exists(dst) or level == 0:
        shutil.copyfile(binary, dst)
        print (indent + '%s => %s' % (binary, dst))

    libs = list(map(str.strip, subprocess.check_output([ldd, binary]).decode('ascii').split('\n')))
    for l in libs:
        if not l: # skip empty line
            continue
        if l == 'statically linked' or l.startswith('linux-vdso.so'):
            continue
        else:
            m = regexp.match(l)
            assert m is not None
            libfile = m.group(2)
            assert libfile.startswith('/')
            assert os.path.isfile(libfile)
            visit(libfile, outdir, visited, level+1)

    return dst


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print ('Usage: %s <binary>' % sys.argv[0])
        exit(1)

    patchelf = shutil.which('patchelf')
    if not patchelf:
        print ('patchelf is not installed. Please install it')
        exit(1)

    my_meme = sys.argv[1]
    outdir = 'out'
    if not os.path.exists(outdir):
        os.mkdir(outdir)

    outfile = visit(my_meme, outdir, set())

    # Fix interpreter so it will use the correct ld and not segfault
    print ('Patching %s interpreter and libc paths' % outfile)
    ld_so = glob.glob(os.path.join(outdir, 'ld-linux-*.so*'))
    print ('Found ld: %s' % ld_so)
    assert len(ld_so) == 1
    ld_so = os.path.basename(ld_so[0])
    interpreter = './' + ld_so
    print ('New interpreter path: %s' % interpreter)

    subprocess.check_output([patchelf, '--set-interpreter', interpreter, '--set-rpath', '.', outfile])

    print ('Create wrapper script')
    real_bin = outfile + '.1'
    shutil.move(outfile, real_bin)
    with open (outfile, 'w') as f:
        f.write("#!/bin/sh\nLD_LIBRARY_PATH=. ./%s $*\n" % os.path.basename(real_bin))

    # chmod everything +x lol
    for f in glob.glob(os.path.join(outdir, '*')):
        st = os.stat(f)
        os.chmod(f, st.st_mode | stat.S_IEXEC)

    print ('Done')
