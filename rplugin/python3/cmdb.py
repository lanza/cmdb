#!/usr/bin/env python3

import socket
import sys
import pynvim


def uint32_from_bytes(data):
    return int.from_bytes(data, byteorder="little")


def string_from_bytes(data):
    return str(bytes)


def read_string_at(data):
    length = uint32_from_bytes(data[0:3])
    if length > 0:
        string = data[4: (4 + length)].decode("ascii")
        return (string, data[(4 + length):])
    else:
        return ("", data[4:])


def read_uint32_at(data):
    return (uint32_from_bytes(data[0:3]), data[4:])


@pynvim.plugin
class Main(object):
    def __init__(self, vim: pynvim.api.nvim.Nvim):
        self.vim = vim

    @pynvim.command('CMDBListen', nargs='1')
    def cmdb_listen(self, *args):
        self.main(args)

    def main(self, args):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(("127.0.0.1", int(args[0][0])))
            while True:
                data = s.recv(4)
                if len(data) == 0:
                    return
                size, data = read_uint32_at(data)
                data = s.recv(size)
                line, data = read_uint32_at(data)
                file, data = read_string_at(data)

                self.vim.command(f"e {file}")
                self.vim.command(f"normal {line}gg")

