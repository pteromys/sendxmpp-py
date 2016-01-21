#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import configparser
import os.path
import sys

import sleekxmpp

from sleekxmpp.thirdparty import GPG

from sleekxmpp.stanza import Message
from sleekxmpp.xmlstream import register_stanza_plugin, ElementBase

class PGPEncrypted(ElementBase):
    name = 'x'
    namespace = 'jabber:x:encrypted'
    plugin_attrib = 'encrypted'
    interfaces = set(['encrypted'])
    lang_interfaces = interfaces

    def set_encrypted(self, data):
        parent = self.parent()
        if data:
            self.xml.text = data
            #parent['body'] = 'This is a XEP-0027 OpenPGP Encrypted Message'
            # shorter
            parent['body'] = 'pgp'
        else:
            del parent['encrypted']

class SendMsgBot(sleekxmpp.ClientXMPP):

    def __init__(self, jid, password, recipients, message, subject, force_pgp, attempt_pgp):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)
        self.recipients = recipients
        self.msg = message
        self.subject = subject
        self.force_pgp = force_pgp
        self.attempt_pgp = attempt_pgp or force_pgp
        self.add_event_handler('session_start', self.start)

        if self.attempt_pgp:
            #self.register_plugin('xep_0027') # Current Jabber OpenPGP Usage

            self.gpg = GPG(gnupghome='',
                        gpgbinary='gpg',
                        use_agent=True,
                        keyring=None)

            register_stanza_plugin(Message, PGPEncrypted)

    def start(self, event):
        #self.send_presence()
        #self.get_roster()
        for recipient in self.recipients:
            message = self.make_message(mto=recipient, msubject=self.subject, mbody=self.msg, mtype='chat')

            if self.attempt_pgp:
                #message['encrypted'].set_encrypted(self.msg)
                enc = self.strip_headers(self.gpg.encrypt(self.msg, recipient))
                message['encrypted'].set_encrypted(enc)
                if self.force_pgp and not enc:
                    print('Error: --force-pgp enabled but encryption to %s failed, does gpg have and trust the key? Aborting...' % recipient)
                    continue

            message.send()
        self.disconnect(wait=True)

    def strip_headers(self, data):
        stripped = []
        begin_headers = False
        begin_data = False
        for line in str(data).splitlines():
            if not begin_headers and 'BEGIN PGP MESSAGE' in line:
                begin_headers = True
                continue
            if begin_headers and line.strip() == '':
                begin_data = True
                continue
            if 'END PGP MESSAGE' in line:
                return '\n'.join(stripped)
            if begin_data:
                stripped.append(line)
        return ''

def FirstOf(*types, error='argument "{}" is not valid'):
    def f(s):
        for t in types:
            try:
                return t(s)
            except:
                pass
        raise argparse.ArgumentTypeError(error.format(s))
    return f

file_or_jid = FirstOf(argparse.FileType('r'),
                      sleekxmpp.basexmpp.JID,
                      error='"{}" is neither a file nor a valid JID')

if __name__ == '__main__':

    p = argparse.ArgumentParser()
    p.add_argument('recipients', metavar='<file or JID>', nargs='+', type=file_or_jid, help='file format is one JID per line')
    p.add_argument('-c', '--config', nargs='?', default=os.path.expanduser('~/.xmpputils'), type=argparse.FileType('r'))
    p.add_argument('-s', '--subject', nargs='?', default='', help='WARNING: subject never encrypted')
    group = p.add_mutually_exclusive_group()
    group.add_argument("-e", "--force-pgp", action="store_true", help='Force OpenPGP encryption for all recipients')
    group.add_argument("-ea", "--attempt-pgp", action="store_true", help='Attempt OpenPGP encryption for all recipients')
    try:
        global_args = p.parse_args()
    except argparse.ArgumentError as e:
        print(e)
        exit(1)
    r = []
    for recipient in global_args.recipients:
        if isinstance(recipient, sleekxmpp.basexmpp.JID):
            r.append(recipient)
        else:
            r.extend(map(sleekxmpp.basexmpp.JID, filter(None, recipient.read().split('\n'))))
    global_args.recipients = r

    conf = configparser.ConfigParser()
    conf.read_file(global_args.config)
    sendxmpp_conf = lambda key: conf.get('sendxmpp', key)

    jid = sleekxmpp.basexmpp.JID(sendxmpp_conf('jid'))
    jid.resource = jid.resource or 'sendxmpp.py'
    xmpp = SendMsgBot(jid, sendxmpp_conf('password'), global_args.recipients, sys.stdin.read(), global_args.subject, global_args.force_pgp, global_args.attempt_pgp)

    if xmpp.connect():
        xmpp.process(block=True)
    else:
        print('Unable to connect.')
        exit(1)
