dstar-gateway-status
====================

This is a quick and dirty D-STAR health script intended to be called by crontab.

It reads in a predefined list of systems (gateways and XRF reflectors) and performs a lookup on various data elements. It's designed to support [Free Star*](http://va3uv.com/freestar.htm) and [ircDDB](http://ircddb.net) systems.
It will not support repeaters on other systems such as stock ICOM G2.
