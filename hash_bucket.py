#!/usr/bin/env python

from string import split
from md5 import md5
import sys

def strreverse(text):
    l = list (text)
    l.reverse()
    return ''.join (l)

def bucket(image):
    m = md5()
    m.update(image)
    s = strreverse(str(int(m.hexdigest()[0:4], 36)))[0:4].lstrip('0')
    if not s:
        return "1"
    else:
        return s

if __name__ == "__main__":
    if len(sys.argv)!=2:
        print "Usage: hash_bucket.py server/file"
        sys.exit(1)
    else:
        (server, filename) = sys.argv[1].split("/")
        print "%s/%s/%s" % (server, bucket(filename), filename)
