dstar-gateway-status
====================

This is a quick and dirty FREE STAR* (D-STAR) health script intended to be called by crontab. It reads in a predefined list of systems (gateways and XRF reflectors) and performs a lookup on various data elements. It's designed to support both full and hybrid [FREE STAR\*](http://va3uv.com/freestar.htm) + [ircDDB](http://ircddb.net) systems.

It will not support repeaters on other systems such as ICOM's G2 software but it will work on FREE STAR* hybrid G2 systems.

Some sites using this script:
 * http://dstar.nv0n.net

Requirements
============

 * Python 2.6 or higher (but not Python 3)
 * python-httplib2

Installation
============

 * Debian/Ubuntu
  1. `sudo apt-get install python-httplib2`
 * CentOS 5.x
  1. `sudo yum install python26 python26-httplib2`
  2. edit gwstatus.py and change the first line from "python" to "python26" as shown in the comment.
