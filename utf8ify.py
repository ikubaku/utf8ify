#!/usr/bin/python

# utf8ify - Convert plaintext file encodings to UTF-8
# 2021 C ikubaku <hide4d51 at gmail.com>
# This program is licensed under The MIT License

import sys
import argparse
import logging
from pathlib import Path


class InputTarget:
    STDIN = 0
    FILE = 1
    def __init__(self, kind, filename=None):
        if kind == InputTarget.FILE and filename is None:
            raise ValueError('Filename is required when creating a file InputTarget.')
        self.kind = kind
        self.filename = filename

    def read(self):
        if self.kind == InputTarget.FILE:
            with open(self.filename, 'rb') as f:
                return f.read()
        else:
            return sys.stdin.read()


class OutputTarget:
    STDOUT = 0
    FILE = 1
    def __init__(self, kind, filename=None):
        if kind == OutputTarget.FILE and filename is None:
            raise ValueError('Filename is required when creating a file OutputTarget.')
        self.kind = kind
        self.filename = filename

    def write(self, data):
        if self.kind == OutputTarget.FILE:
            with open(self.filename, 'wb') as f:
                f.write(data)
        else:
            sys.stdout.write(data)


class UTF8ifier:
    def __init__(self, input_target, output_target, use_chardet, given_input_encoding=None):
        self.input_target = input_target
        self.output_target = output_target
        self.use_chardet = use_chardet
        self.given_input_encoding = given_input_encoding
        if use_chardet:
            from chardet.universaldetector import UniversalDetector
            self.guesser = UniversalDetector()
        else:
            self.guesser = None

    def determine_encoding(self, data):
        self.guesser.feed(data)
        res = self.guesser.close()
        if self.guesser.done:
            self.input_encoding = res['encoding']
        else:
            if self.given_input_encoding is None:
                return -1
            else:
                self.input_encoding = self.given_input_encoding
                return 0

    def convert(self):
        input_data = self.input_target.read()
        if self.use_chardet:
            if self.determine_encoding(input_data) == -1:
                logging.error('Could not determine the input encoding.')
                return -1
        try:
            output_data = input_data.decode(encoding=self.input_encoding).encode()
        except UnicodeError as ex:
            logging.error('Could not convert the input.')
            logging.error('Exception: {}'.format(str(ex)))
            return -1
        self.output_target.write(output_data)
        return 0

def main():
    parser = argparse.ArgumentParser(description='utf8ify - Convert plaintext file encodings to UTF-8')
    parser.add_argument('-e', '--encoding', help='encoding of the input', metavar='ENCODING')
    parser.add_argument('--nochardet', help='do not use chardet for guessing the input encoding', action='store_true')
    parser.add_argument('-o', '--output', help='output filename (write to stdout if not specified)', metavar='OUTPUT')
    parser.add_argument('input', help='input filename (read from stdin if `-` is specified)', metavar='INPUT')

    args = parser.parse_args()

    if args.input is None:
        logging.error('The input is not specified.')
        return -1
    if args.encoding is None and args.nochardet:
        logging.error('No hint for input encoding is given.')
        logging.error('Specify the input encoding or remove the --nochardet option.')
        return -1

    if args.input == '-':
        input_target = InputTarget(InputTarget.STDIN)
    else:
        input_path = Path(args.input).expanduser()
        input_target = InputTarget(InputTarget.FILE, input_path)

    if args.output is None:
        output_target = OutputTarget(OutputTarget.STDOUT)
    else:
        output_path = Path(args.output).expanduser()
        output_target = OutputTarget(OutputTarget.FILE, output_path)

    converter = UTF8ifier(
        input_target,
        output_target,
        not args.nochardet,
        args.encoding
    )

    return converter.convert()

if __name__ == '__main__':
    sys.exit(main())
