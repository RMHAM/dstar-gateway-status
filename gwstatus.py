#!/usr/bin/python
# Hack by Joey Stanford <nv0n@arrl.net>

import subprocess
from time import ctime
import httplib
import string


def main():
    systems = {"W0DK": "Boulder",
               "W0CDS": "Devil's Head",
               "W0TLM": "Monument",
               "XRF719": "XRF719 Reflector",
               "WR0AEN": "Squaw Mountain",
               "W0BFD": "Fort Collins",
               "KD0LUX": "RT Systems Testbed",
               "KC0CVU": "Colorado Springs",
               "KD0QPG": "Salida",
               "KD0RED": "Grand Junction",
               "KC7SNO": "Cheyenne",
               "NE7WY": "Gillette"}

    # HTML vars
    startline = "<TD BGCOLOR=#EEEEEE>"
    endline = "</TD>\n"
    down = '<B><FONT COLOR="#CC0000">OFFLINE</FONT></B></TD>\n'
    broken = '<B><FONT COLOR="#FFA500">BROKEN</FONT></B></TD>\n'
    up = '<B><FONT COLOR="#00BB00">ONLINE</FONT></B></TD>\n'
    details = '<a href="http://status.ircddb.net/qam.php? \
              call=CALLSIGN">CALLSIGN</a>'

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
    startstr = string.find(data1, ': ')+2
    endstr = string.find(data1, '</b')
    myip = data1[startstr:endstr]

    subprocess.call(["rm", "gwys.txt"])
    subprocess.call(["wget", "http://www.va3uv.com/gwys.txt"])

    gwys = open("gwys.txt", "r")

    header = open("gwstatus.hdr", "r")

    html = open("/usr/local/var/www/htdocs/index.html", "w")

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
            callsign, ip, port = line.split()
        elif len(line.split()) == 2:
            callsign, port = line.split()
            ip = "[blank]"
        else:
            continue
        if callsign in systems:
            print callsign
            # start
            html.write("<TR>\n")
            # callsign
            html.write(startline)
            html.write(details.replace("CALLSIGN", callsign))
            html.write(endline)
            # status
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
                    html.write(up)
                elif res.status == 503:
                    html.write(down)
                else:
                    html.write(broken.replace("BROKEN", res.status))
            # location
            html.write(startline)
            html.write(systems[callsign])
            html.write(endline)
            # IP
            html.write(startline)
            html.write(ip)
            html.write(endline)
            # detailed status
            html.write(startline)
            if ip == "[blank]":
                html.write("No IP Address")
            else:
                html.write(res.reason)
            html.write(endline)

    # finish up
    html.write("</TABLE>\n")
    html.write("</BODY>\n")
    html.write("</HTML>\n")
    gwys.close()
    header.close()
    html.close()

if __name__ == "__main__":
        main()
