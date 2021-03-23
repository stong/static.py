# static.py

### What does it do?

You give it a dynamically linked binary and it will make a directory that has all the dependencies (recursively). It also fixes the ld interpreter and libc paths so it will not segfault

### How does it work?

It recursively calls ldd and copies all the required .so files. Then, it also needs to patch up the ld interpreter so it will not try to use the system ld rather than the one copied from the source host.

### How do I use it

For example, making a redistributable imagemagick:

`./lmao.py /usr/bin/convert`

### Should I use this in production?

Yes and please email me so I can short your company stock. (Not financial advice btw)
