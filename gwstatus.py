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


def get_IP():
    # determine our external ip
    ip_regex = '([\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3})'
    conn = httplib.HTTPConnection("checkip.dyndns.org")
    conn.request("GET", "")
    res = conn.getresponse()
    if res.status == 200:
        ip = re.split(ip_regex, res.read())[1]
    else:
        print 'Error connecting to the server!! Check your internet connection'
        exit()
    conn.close()
    return ip


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

    myip = get_IP()

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
        # retrieve gwys information
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
            # Let's get the ircddb status next.
            if callsign.startswith("XRF"):
                # no ddns yet
                ircddbip = "[blank]"
            else:
                ircddbgw = callsign.lower() + ".gw.ircddb.net"
                try:
                    ircddbip = socket.gethostbyname(ircddbgw)
                except socket.gaierror:
                    ircddbip = "[blank]"
            # start of html file
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
            if ip == myip:
                html.write(broken.replace("BROKEN", "SELF"))
            elif (ip == "[blank]" and ircddbip == "[blank]"):
                html.write(down)
            else:
                try:
                    if ip == "[blank]":
                        conn = httplib.HTTPConnection(ircddbip)
                    else:
                        conn = httplib.HTTPConnection(ip)
                    conn.request("HEAD", "/")
                    res = conn.getresponse()
                    conn.close()
                except socket.error, e:
                    resstatus = 408
                    resreason = httplib.responses[408]
                else:
                    resstatus = res.status
                    resreason = res.reason
                if resstatus == 200:
                    if ip == "[blank]":
                        linked_ip = \
                            '<a href="http://' + ircddbip + '">ONLINE</a>'
                    else:
                        linked_ip = '<a href="http://' + ip + '">ONLINE</a>'
                    html.write(up.replace("ONLINE", linked_ip))
                elif (resstatus == 503 or resstatus == 408):
                    html.write(down)
                else:
                    html.write(broken.replace("BROKEN", resreason))
            # ping status
            html.write(startline)
            if (ip == "[blank]" and ircddbip == "[blank]"):
                html.write(down)
            elif ip == myip:
                html.write(broken.replace("BROKEN", "SELF"))
            else:
                if ip == "[blank]":
                    if ping(ircddbip) == 0:
                        html.write(up)
                    else:
                        html.write(down)
                elif ping(ip) == 0:
                    html.write(up)
                else:
                    html.write(down)
            # location
            html.write(startline)
            html.write(systems[callsign])
            html.write(endline)
            # IP
            html.write(startline)
            if ip == "[blank]":
                html.write(broken)
            else:
                html.write(ip)
            html.write(endline)
            # ircddb ddns
            html.write(startline)
            if callsign.startswith("XRF"):
                # no ddns yet
                html.write("[N/A]")
                html.write(endline)
            else:
                if ircddbip == "[blank]":
                    html.write(down.replace("OFFLINE", "NOT FOUND"))
                # exists and matches gwys.txt
                # or exists but gwys.txt is broken
                elif (ircddbip == ip or ip == "[blank]"):
                    html.write(up)
                else:
                # exists and is different
                    html.write(broken)
            # ddns ip
            html.write(startline)
            if ircddbip == "[blank]":
                html.write(broken)
            else:
                html.write(ircddbip)
            html.write(endline)
            # detailed web status
            html.write(startline)
            if ip == "[blank]":
                html.write("No IP Address")
            else:
                html.write(resreason)
            html.write(endline)

    # let's check to see if any where not in the gwy file
    unprocessed = systems_set - processed_set
    if len(unprocessed) > 0:
        html.write("</TABLE>\n\n")
        html.write("<P>Hosts Not Found</P>\n")
        html.write("<TABLE BORDER CELLPADDING=5>")
        html.write("<TR VALIGN=top>")
        html.write("<TD BGCOLOR=#EEEEEE><B>Host</B></TD>")
        html.write("<TD BGCOLOR=#EEEEEE><B>Location</B></TD>")
        html.write("</TR>\n")
        for item in unprocessed:
            print item
            html.write("<TR>\n")
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
    import re
    import ConfigParser
    import socket

    configfile = "gwstatus.ini"

    config = readConfigFile(configfile)

    main()
