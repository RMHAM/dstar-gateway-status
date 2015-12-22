[![Code Issues](https://www.quantifiedcode.com/api/v1/project/ba02492aeb5041229b85085fdd049e51/badge.svg)](https://www.quantifiedcode.com/app/project/ba02492aeb5041229b85085fdd049e51)

Description
===========

This is a quick and dirty FREE STAR* (D-STAR) health and status script which generates an HTML page. It reads in a predefined list of systems (gateways and XRF reflectors) and performs a lookup on various data elements. It's designed to support both full and hybrid [FREE STAR\*](http://va3uv.com/freestar.htm) + [ircDDB](http://ircddb.net) systems.

It will not support repeaters on other systems such as ICOM's G2 software running DPLUS. It may be useful for repeaters that utilize ircDDB but are not fully FREE STAR* compliant.

Example
=======
![Example Screenshot](https://github.com/RMHAM/dstar-gateway-status/blob/master/screenshot.png)

Some sites using this script:
 * http://dstar.nv0n.net
 * https://wb1gof.dstargateway.org/gwstatus.html

Requirements
============

 * Python 2.6 or higher (but not Python 3)
 * python-httplib2

Prerequisites
=============

 * Debian/Ubuntu
  1. `sudo apt-get install python-httplib2`
 * CentOS 5.x
  1. `sudo yum install python26 python26-httplib2`
  2. edit gwstatus.py and change the first line from "python" to "python26" as shown in the comment.

Configuration
=============
Edit gwstatus.ini:
 * set list of repeaters and reflectors you wish to monitor
 * set the destination location (`htmlout`) of the resulting html file

Edit gwstatus.hdr:
 * customize to meet your needs

Execution
=========
This script was designed to be run nightly from cron. For example: `@daily /home/joey/gwstatus.py > /home/joey/gwstatus.log`

This script does not need root so long as the user executing the script has priviledges to write to the directory you specified in gwstatus.ini.
