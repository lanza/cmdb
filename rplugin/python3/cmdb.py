#!/usr/bin/env python3

import socket
import sys
import pynvim
from enum import Enum
import _thread

class IDEType(Enum):
    Error = 0
    FileAndLocation = 1
    VariableEvaluation = 2


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

def encode_unsigned(i: int) -> bytes:
    return i.to_bytes(4, byteorder="little")

def encode_string(s: str) -> bytes:
    length = len(s)
    data = encode_unsigned(length) + s.encode('ascii')
    return data

def encode_info(*args):
    d = bytes()
    for arg in args:
        t = type(arg)
        if t is int:
            d += encode_unsigned(arg)
        elif t is str:
            d += encode_string(arg)
        else:
            print(f"Bad encode_info: {arg} {t}")

    return d


VIM = None

def adjust_line(*args):
    VIM.command(f"e {args[1]}")
    VIM.command(f"normal {args[0]}gg")


def echo_variable(*args):
    VIM.command(f"echom \"{args[0]}\"")


def listen_main(name, s, vim):
    while True:
        data = s.recv(8)
        if len(data) == 0:
            return
        t, data = read_uint32_at(data)
        size, data = read_uint32_at(data)
        data = s.recv(size)

        if t == IDEType.FileAndLocation.value:
            line, data = read_uint32_at(data)
            file, data = read_string_at(data)
            vim.async_call(adjust_line, line, file)
        elif t == IDEType.VariableEvaluation.value:
            value, data = read_string_at(data)
            vim.async_call(echo_variable, value)

@pynvim.plugin
class Main(object):
    def __init__(self, vim: pynvim.api.nvim.Nvim):
        global VIM
        VIM = vim
        self.vim = vim


    @pynvim.command('CMDBListen', nargs='1')
    def cmdb_listen(self, *args):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect(("127.0.0.1", int(args[0][0])))
        _thread.start_new_thread(listen_main, ("listen", self.s, self.vim))


    @pynvim.command('CMDBExpression', nargs='1')
    def cmdb_expression(self, *args):
        self.s.send(encode_unsigned(len(args[0][0]) + 4))
        self.s.send(encode_info(str(args[0][0])))



