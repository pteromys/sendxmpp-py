# sendxmpp-py

`sendxmpp` is the XMPP equivalent of sendmail. It is an alternative to the old sendxmpp written in Perl.

Dependencies:

- python 3
- dnspython
- sleekxmpp

To install them on Ubuntu:

    sudo apt-get install python3 python3-pip
    sudo pip install dnspython sleekxmpp

[Arch AUR package](https://aur.archlinux.org/packages/sendxmpp-py/)

Installation: just put the script wherever you want.

Configuration: `cp sendxmpp.cfg ~/.config/` and edit `~/.config/sendxmpp.cfg` with your XMPP credentials

Usage examples:

- `echo "This is a test" | sendxmpp user@host`
- `sendxmpp user@host <README.md`

License
-------
GNU/GPLv3 - Check LICENSE.md for details