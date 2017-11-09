#!/usr/bin/env python
# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2007 Agendaless Consulting and Contributors.
# All Rights Reserved.
#
# Copyright (c) 2017 Sudhindra Bhat
#
# This software is subject to the provisions of the BSD-like license at
# http://www.repoze.org/LICENSE.txt.  A copy of the license should accompany
# this distribution.  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL
# EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND
# FITNESS FOR A PARTICULAR PURPOSE
#
##############################################################################

# A event listener meant to be subscribed to PROCESS_STATE_CHANGE
# events.  It will send sms or make phone calls when processes that are children of
# supervisord transition unexpectedly to the EXITED state.

# A supervisor config snippet that tells supervisor to use this script
# as a listener is below.





import copy
import os
import sys

from superlance.process_state_monitor import ProcessStateMonitor
from supervisor import childutils


class SuperTwill(ProcessStateMonitor):
    process_state_events = ['PROCESS_STATE_FATAL']

    @classmethod
    def _get_opt_parser(cls):
        from optparse import OptionParser

        parser = OptionParser()
        parser.add_option("-t", "--token", help="Twilio Token")
        parser.add_option("-m", "--mode", help="call/sms/both")
        parser.add_option("-n", "--hostname", help="System Hostname")

        return parser

    @classmethod
    def parse_cmd_line_options(cls):
        parser = cls._get_opt_parser()
        (options, args) = parser.parse_args()
        return options

    @classmethod
    def validate_cmd_line_options(cls, options):
        parser = cls._get_opt_parser()
        if not options.token:
            parser.print_help()
            sys.exit(1)
        if not options.mode:
            parser.print_help()
            sys.exit(1)
        if not options.hostname:
            import socket
            options.hostname = socket.gethostname()

        validated = copy.copy(options)
        return validated

    @classmethod
    def get_cmd_line_options(cls):
        return cls.validate_cmd_line_options(cls.parse_cmd_line_options())

    @classmethod
    def create_from_cmd_line(cls):
        options = cls.get_cmd_line_options()

        if 'SUPERVISOR_SERVER_URL' not in os.environ:
            sys.stderr.write('Must run as a supervisor event listener\n')
            sys.exit(1)

        return cls(**options.__dict__)

    def __init__(self, **kwargs):
        ProcessStateMonitor.__init__(self, **kwargs)
        self.mode = kwargs['mode']
        self.token = kwargs['token']
        self.hostname = kwargs.get('hostname', None)

    def get_process_state_change_msg(self, headers, payload):
        pheaders, pdata = childutils.eventdata(payload + '\n')
        txt = ("[{0}] Process {groupname}:{processname} "
               "failed to start too many times".format(self.hostname, **pheaders))
        return txt

    def send_batch_notification(self):
        pass



def main():
    supertwill = SuperTwill.create_from_cmd_line()
    supertwill.run()

if __name__ == '__main__':
    main()