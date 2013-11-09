#!/usr/bin/python
"""Check Gateway Health."""
# Joey Stanford <nv0n@arrl.net>


def readConfigFile(configfile):
    config = ConfigParser.ConfigParser()
    try:
        config.read(configfile)
    except:
        print 'Config File Error:', err
        exit(0)
    return config


def ping(ip):
    ret = subprocess.call("ping -c 1 %s" % ip,
                          shell=True,
                          stdout=open('/dev/null', 'w'),
                          stderr=subprocess.STDOUT)
    return(ret)


def main():

    # load up the systems we want to interrogate
    systems = {}
    for callsign, location in config.items("systems"):
        systems[callsign.upper()] = location

    # we need to cover the case where a system we care about doesn't
    # exist yet in the gateway file. We'll do this via sets.
    # set(systems) only adds the key (callsign)
    systems_set = set(systems)
    processed_set = set()

    # HTML vars
    startline = "<TD BGCOLOR=#EEEEEE>"
    endline = "</TD>\n"
    down = '<B><FONT COLOR="#CC0000">OFFLINE</FONT></B></TD>\n'
    broken = '<B><FONT COLOR="#FFA500">BROKEN</FONT></B></TD>\n'
    up = '<B><FONT COLOR="#00BB00">ONLINE</FONT></B></TD>\n'
    details = ('<a href='
               '"http://status.ircddb.net/qam.php?call=CALLSIGN"'
               '>CALLSIGN</a>')

    # determine our external ip
    conn = httplib.HTTPConnection("checkip.dyndns.org")
    conn.request("GET", "/index.html")
    res = conn.getresponse()
    if res.status == 200:
        data1 = res.read()
    else:
        print 'Error connecting to the server!! Check your internet connection'
        exit()
    conn.close()
    startstr = string.find(data1, ': ') + 2
    endstr = string.find(data1, '</b')
    myip = data1[startstr:endstr]

    subprocess.call(["rm", config.get("files", "gwysfile")])
    subprocess.call(["wget", config.get("files", "gwysdownload")])

    gwys = open(config.get("files", "gwysfile"), "r")

    header = open(config.get("files", "header"), "r")

    html = open(config.get("files", "htmlout"), "w")

    # write out header
    for line in header.readlines():
        html.write(line)
    html.write("\n")
    html.write("<P><SMALL>")
    html.write("Last Updated: ")
    html.write(ctime())
    html.write("</SMALL></P>")
    html.write("\n")

    # write out body
    for line in gwys.readlines():
        if len(line.split()) == 3:
            callsign, ip, _ = line.split()
        elif len(line.split()) == 2:
            callsign, _ = line.split()
            ip = "[blank]"
        else:
            continue
        if callsign in systems:
            print callsign
            processed_set.add(callsign)
            # start
            html.write("<TR>\n")
            # callsign
            html.write(startline)
            if callsign.startswith("XRF"):
                # XRF not handled by ircddb
                html.write(callsign)
            else:
                html.write(details.replace("CALLSIGN", callsign))
            html.write(endline)
            # dashboard status
            html.write(startline)
            if ip == "[blank]":
                html.write(broken)
            elif ip == myip:
                html.write(broken.replace("BROKEN", "SELF"))
            else:
                conn = httplib.HTTPConnection(ip)
                conn.request("HEAD", "/")
                res = conn.getresponse()
                conn.close()
                if res.status == 200:
                    linked_ip = '<a href="http://' + ip + '">ONLINE</a>'
                    html.write(up.replace("ONLINE", linked_ip))
                elif res.status == 503:
                    html.write(down)
                else:
                    html.write(broken.replace("BROKEN", res.status))
            # ping status
            html.write(startline)
            if ip == "[blank]":
                html.write(broken)
            elif ip == myip:
                html.write(broken.replace("BROKEN", "SELF"))
            else:
                if ping(ip) == 0:
                    html.write(up)
                else:
                    html.write(down)
            # location
            html.write(startline)
            html.write(systems[callsign])
            html.write(endline)
            # IP
            html.write(startline)
            html.write(ip)
            html.write(endline)
            # ircddb ddns
            html.write(startline)
            if callsign.startswith("XRF"):
                # no ddns yet
                ircddbip = "[blank]"
                html.write("[N/A]")
                html.write(endline)
            else:
                ircddbgw = callsign.lower() + ".gw.ircddb.net"
                try:
                    ircddbip = socket.gethostbyname(ircddbgw)
                except socket.gaierror:
                    ircddbip = "[blank]"
                if ircddbip == "[blank]":
                    html.write(down.replace("OFFLINE", "NOT FOUND"))
                elif ircddbip == ip:
                    html.write(up)
                else:
                # exists and is different
                    html.write(broken)
            # ddns ip
            html.write(startline)
            html.write(ircddbip)
            html.write(endline)
            # detailed web status
            html.write(startline)
            if ip == "[blank]":
                html.write("No IP Address")
            else:
                html.write(res.reason)
            html.write(endline)

    # let's check to see if any where not in the gwy file
    unprocessed = systems_set - processed_set
    if len(unprocessed) > 0:
        html.write("</TABLE>\n\n")
        html.write("<P>Hosts Not Found</P>")
        html.write("<TABLE BORDER CELLPADDING=5>")
        html.write("<TR VALIGN=top>")
        html.write("<TD BGCOLOR=#EEEEEE><B>Host</B></TD>")
        html.write("<TD BGCOLOR=#EEEEEE><B>Location</B></TD>")
        html.write("</TR>")
        for item in unprocessed:
            print item
            # callsign
            html.write(startline)
            html.write(broken.replace("BROKEN", item))
            html.write(endline)
            # location
            html.write(startline)
            html.write(systems[item])
            html.write(endline)

    # finish up
    html.write("</TABLE>\n")
    html.write("</BODY>\n")
    html.write("</HTML>\n")
    gwys.close()
    header.close()
    html.close()

if __name__ == "__main__":
    import subprocess
    from time import ctime
    import httplib
    import string
    import ConfigParser
    import socket

    configfile = "gwstatus.ini"

    config = readConfigFile(configfile)

    main()
