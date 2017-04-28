#!/usr/bin/env python
# coding: utf-8

from wsgiref.simple_server import make_server
from app import application


def main():
    httpd = make_server('', 8000, application)
    print "Serving HTTP on port 8000..."
    httpd.serve_forever()


if __name__ == '__main__':
    main()
