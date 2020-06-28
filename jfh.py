#!/usr/bin/python3

import argparse

from jf_parser import JenkinsFileParser
from helper import JenkinsFileHelper


def configure_argparse():
    parser = argparse.ArgumentParser(description='Script to help manage JenkinsfIles')
    parser.add_argument('-f', '--filename', dest='filename', default='Jenkinsfile')
    #  parser.add_argument('command', metavar='command', type=str,
    #                      help='command')
    sub = parser.add_subparsers(dest='command', help='command to run')
    a = sub.add_parser('cs')
    sub.add_parser('ls')
    a.add_argument('stage_name')
    return parser.parse_args()


if __name__ == "__main__":
    args = configure_argparse()
    p = JenkinsFileParser(args.filename)
    h = JenkinsFileHelper(p)
    if args.command == 'ls':
        h.print_stages()
    if args.command == 'cs':
        h.process_stage_by_id(args.stage_name)
        h.print_stages()
