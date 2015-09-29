"""Setup to process multiple repos."""
# =============================================================================
# CONTENTS
# -----------------------------------------------------------------------------
# abdi_processrepos
#
# Public Functions:
#   addCommonParserArgs
#   setupParser
#   process
#
# -----------------------------------------------------------------------------
# (this contents block is generated, edits will be lost)
# =============================================================================

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os

import phlmail_sender
import phlsys_sendmail

import abdt_exhandlers
import abdt_logging

import abdi_processrepoarglist


def addCommonParserArgs(parser):
    parser.add_argument(
        '--arcyd-email',
        metavar="EMAIL",
        type=str,
        required=True,
        help="email address for arcyd to send messages from")
    parser.add_argument(
        '--sendmail-binary',
        metavar="PROGRAM",
        type=str,
        default="sendmail",
        help="program to send the mail with (e.g. sendmail, catchmail)")
    parser.add_argument(
        '--sendmail-type',
        metavar="TYPE",
        type=str,
        default="sendmail",
        help="type of program to send the mail with (sendmail, catchmail), "
        "this will affect the parameters that Arcyd will use.")
    parser.add_argument(
        '--sleep-secs',
        metavar="TIME",
        type=int,
        default=3,
        help="time to wait between runs through the list")
    parser.add_argument(
        '--external-report-command',
        metavar="PATH",
        type=str,
        default=None,
        help="path to an external reporter to send monitoring info to, "
             "will be called like so: $REPORTER <<json report object>>")
    parser.add_argument(
        '--max-workers',
        metavar="COUNT",
        type=int,
        default=0,
        help="maximum number of worker processes to run at one time, Set to 0 "
             "to let Arcyd decide the number. Set to 1 to disable "
             "multiprocessing completely.")


def setupParser(parser):
    addCommonParserArgs(parser)
    parser.add_argument(
        '--sys-admin-emails',
        metavar="EMAIL",
        nargs="+",
        type=str,
        required=True,
        help="email addresses to send important system events to")
    parser.add_argument(
        '--no-loop',
        action='store_true',
        help="supply this argument to only process each repo once then exit")
    parser.add_argument(
        '--external-error-logger',
        metavar="PATH",
        type=str,
        default=None,
        help="path to an external logger to send errors to, will be called "
             "like so: $LOGGER '<<identifier>>' '<<full details>>'")
    parser.add_argument(
        '--overrun-secs',
        metavar="SECONDS",
        type=int,
        default=60,
        help="number of seconds to wait before starting the next cycle and "
             "leaving active jobs behind.")


def process(args, repo_configs):

    if args.sendmail_binary:
        phlsys_sendmail.Sendmail.set_default_binary(
            args.sendmail_binary)

    if args.sendmail_type:
        phlsys_sendmail.Sendmail.set_default_params_from_type(
            args.sendmail_type)

    mail_sender = phlmail_sender.MailSender(
        phlsys_sendmail.Sendmail(), args.arcyd_email)

    if args.external_error_logger:
        full_path = os.path.abspath(args.external_error_logger)
        abdt_logging.set_external_system_error_logger(full_path)

    on_exception = abdt_exhandlers.make_exception_message_handler(
        args.sys_admin_emails,
        None,
        "arcyd stopped with exception",
        "")

    return _processrepolist(
        args, repo_configs, on_exception, mail_sender)


def _processrepolist(
        args, repo_configs, on_exception, mail_sender):
    try:
        return abdi_processrepoarglist.do(
            repo_configs,
            args.sys_admin_emails,
            args.sleep_secs,
            args.no_loop,
            args.external_report_command,
            mail_sender,
            args.max_workers,
            args.overrun_secs)
    except BaseException:
        on_exception("Arcyd will now stop")
        print("stopping")
        raise


# -----------------------------------------------------------------------------
# Copyright (C) 2013-2015 Bloomberg Finance L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------ END-OF-FILE ----------------------------------
