#!/usr/bin/python
# CENTOS 5.x users use #!/usr/bin/python26
"""Check Gateway Health."""
# Joey Stanford <nv0n@arrl.net>

from Queue import Queue
from threading import Thread


class NetWorker(Thread):
    """Defines the Worker which does all the work"""

    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue

    def run(self):
        """Let's run the worker"""
        while True:
            # Get the work from the queue and expand the tuple
            systems, repeater, myip = self.queue.get()
            check_ircddb(systems, repeater)
            check_single_dashboard(systems, repeater, myip)
            check_pingable(systems, repeater, myip)
            self.queue.task_done()


class Repeater(object):
    """Repeater Details Object"""

    def __init__(self, callsign, location):
        self.callsign = callsign.upper()
        self.location = location
        self.dashboard = ""
        self.pingable = ""
        self.ip = ""
        self.ircddbip = ""
        self.web_status = ""
        self.in_gwys_file = False


def readconfigfile(configfile):
    """setup the config file"""
    config = ConfigParser.ConfigParser()
    try:
        config.read(configfile)
    except ConfigParser.Error, err:
        print 'Config File Error:', err
        exit(1)
    return config


def ping(ip):
    """perform a safe ping"""
    ret = subprocess.call("ping -c 1 %s" % ip,
                          shell=True,
                          stdout=open('/dev/null', 'w'),
                          stderr=subprocess.STDOUT)
    return (ret)


def get_ip():
    """determine our external ip"""
    ip_regex = '([\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3})'
    conn = httplib.HTTPConnection("checkip.dyndns.org", timeout=30)
    conn.request("GET", "")
    res = conn.getresponse()
    if res.status == 200:
        ip = re.split(ip_regex, res.read())[1]
    else:
        print 'Error connecting to the server!! Check your internet connection'
        exit()
    conn.close()
    return ip


def process_gwys_file(gwys, systems):
    """read gateway file and extract data we care about"""

    for line in gwys.readlines():
        if len(line.split()) == 3:
            callsign, ip, _ = line.split()
        elif len(line.split()) == 2:
            callsign, _ = line.split()
            ip = ""
        else:
            print "Bad gwys.txt line: %s" % (line)
            continue

        callsign = callsign.upper()
        if callsign in systems:
            systems[callsign].in_gwys_file = True
            systems[callsign].ip = ip


def check_ircddb(systems, repeater):
    """check ircddb status"""
    if (repeater.startswith("XRF") or repeater.startswith("REF")):
        # no ddns yet
        systems[repeater].ircddbip = ""
    else:
        ircddbgw = repeater.lower() + ".gw.ircddb.net"
        try:
            systems[repeater].ircddbip = socket.gethostbyname(ircddbgw)
        except socket.gaierror:
            systems[repeater].ircddbip = ""


def check_single_dashboard(systems, repeater, myip):
    """check the dashboard of each repeater"""

    if systems[repeater].ip == myip:
        systems[repeater].dashboard = "SELF"
        systems[repeater].web_status = "N/A"
    elif (systems[repeater].ip == "" and systems[repeater].ircddbip == ""):
        systems[repeater].dashboard = "OFFLINE"
        systems[repeater].web_status = "No IP Addresss"
    else:
        # let's see if we can connect using one of the IPs
        try:
            if systems[repeater].ip == "":
                conn = httplib.HTTPConnection(systems[repeater].ircddbip,
                                              timeout=30)
            else:
                conn = httplib.HTTPConnection(systems[repeater].ip, timeout=30)
            conn.request("HEAD", "/")
            res = conn.getresponse()
            conn.close()
        except socket.error:
            resstatus = 408
        except httplib.BadStatusLine:
            resstatus = 204
        else:
            resstatus = res.status

        # Let's interpret the results
        if resstatus == 200:
            systems[repeater].dashboard = "ONLINE"
        elif (resstatus in [503, 408]):
            systems[repeater].dashboard = "OFFLINE"
        else:
            # Broken systems e.g. "No Content"
            systems[repeater].dashboard = httplib.responses[resstatus]

        # set the web status as our parting gift
        systems[repeater].web_status = str(resstatus)


def check_pingable(systems, repeater, myip):
    """Can we even reach the system?"""

    if (systems[repeater].ip == "" and systems[repeater].ircddbip == ""):
        systems[repeater].pingable = "BROKEN"
    elif systems[repeater].ip == myip:
        systems[repeater].pingable = "SELF"
    elif (systems[repeater].ip == "" and systems[repeater].ircddbip != ""):
        if ping(systems[repeater].ircddbip) == 0:
            systems[repeater].pingable = "ONLINE"
        else:
            systems[repeater].pingable = "OFFLINE"
    elif ping(systems[repeater].ip) == 0:
        systems[repeater].pingable = "ONLINE"
    else:
        systems[repeater].pingable = "OFFLINE"


def generate_html(systems):
    """Generate the HTML file"""

    keylist = systems.keys()
    keylist.sort()

    # HTML vars
    startline = "<TD BGCOLOR=#EEEEEE>"
    endline = "</TD>\n"
    down = '<B><FONT COLOR="#CC0000">OFFLINE</FONT></B></TD>\n'
    broken = '<B><FONT COLOR="#FFA500">BROKEN</FONT></B></TD>\n'
    up = '<FONT COLOR="#00BB00">ONLINE</FONT></TD>\n'
    details = ('<a href='
               '"http://status.ircddb.net/qam.php?call=CALLSIGN"'
               '>CALLSIGN</a>')

    with open(config.get("files", "htmlout"), "w") as html:

        with open(config.get("files", "header"), "r") as header:
            # write out header
            for line in header.readlines():
                html.write(line)

        html.write("\n")
        html.write("<P><SMALL>")
        html.write("Last Updated: ")
        html.write(ctime())
        html.write("</SMALL></P>")
        html.write("\n")

        # write out collected data
        # for repeater in systems:
        for repeater in keylist:
            html.write("<TR>\n")

            # callsign
            html.write(startline)
            if (systems[repeater].callsign.startswith("XRF")
                    or systems[repeater].callsign.startswith("REF")):
                # XRF & REF not handled by ircddb
                html.write(systems[repeater].callsign)
            else:
                html.write(
                    details.replace("CALLSIGN", systems[repeater].callsign))
            html.write(endline)

            # dashboard status
            html.write(startline)
            if systems[repeater].dashboard == "SELF":
                html.write(broken.replace("BROKEN", "SELF"))
            elif systems[repeater].dashboard == "OFFLINE":
                html.write(down)
            elif systems[repeater].dashboard == "ONLINE":
                if systems[repeater].ip == "":
                    linked_ip = \
                        '<a href="http://' + \
                        systems[repeater].ircddbip + \
                        '">ONLINE</a>'
                else:
                    linked_ip = \
                        '<a href="http://' + \
                        systems[repeater].ip + \
                        '">ONLINE</a>'
                html.write(up.replace("ONLINE", linked_ip))
            else:
                html.write(
                    broken.replace("BROKEN", systems[repeater].dashboard))
            # ping status
            html.write(startline)
            if systems[repeater].pingable == "OFFLINE":
                html.write(down)
            elif systems[repeater].pingable == "BROKEN":
                html.write(broken)
            elif systems[repeater].pingable == "SELF":
                html.write(broken.replace("BROKEN", "SELF"))
            elif systems[repeater].pingable == "ONLINE":
                html.write(up)
            else:
                html.write(broken)

            # location
            html.write(startline)
            html.write(systems[repeater].location)
            html.write(endline)

            # IP
            html.write(startline)
            if systems[repeater].ip == "":
                if systems[repeater].in_gwys_file:
                    html.write(broken)
                else:
                    html.write(broken.replace("BROKEN", "MISSING"))
            elif (systems[repeater].callsign.startswith("XRF")
                  or systems[repeater].callsign.startswith("REF")
                  or (systems[repeater].ip == systems[repeater].ircddbip)):
                html.write(up.replace("ONLINE", systems[repeater].ip))
            else:
                html.write(broken.replace("BROKEN", systems[repeater].ip))
            html.write(endline)

            # ddns ip
            html.write(startline)
            if (systems[repeater].callsign.startswith("XRF")
                    or systems[repeater].callsign.startswith("REF")):
                # no ddns yet
                html.write("[N/A]")
            else:
                if systems[repeater].ircddbip == "":
                    html.write(down)
                elif systems[repeater].ircddbip == systems[repeater].ip:
                    html.write(up.replace("ONLINE",
                                          systems[repeater].ircddbip))
                else:
                    html.write(
                        broken.replace("BROKEN", systems[repeater].ircddbip))
            html.write(endline)

            # detailed web status
            html.write(startline)
            html.write(
                ("<a href='https://http.cat/" + systems[repeater].web_status +
                 "'>" + systems[repeater].web_status + "</a>"))
            html.write(endline)

        # finish up
        html.write("</TABLE>\n")
        html.write("</BODY>\n")
        html.write("</HTML>\n")


def main():
    """Main Function"""

    # load up the systems we want to interrogate
    systems = {}
    for callsign, location in config.items("systems"):
        systems[callsign.upper()] = Repeater(callsign, location)

    # grab our IP so we can know if we're running the script
    # on the same IP as a systems[repeater].and indicate as such
    myip = get_ip()

    # remove old gwysfile from previous run and download the latest
    # copy
    subprocess.call(["rm", config.get("files", "gwysfile")])
    subprocess.call(["wget", config.get("files", "gwysdownload")])

    # read in gateways
    with open(config.get("files", "gwysfile"), "r") as gwys:
        process_gwys_file(gwys, systems)

    # Net operations take time so we're going to have each repeater
    # have it's own worker thread to speed up the process
    # Create a queue to communicate with the worker threads
    queue = Queue()

    # Create 1 worker thread for each repeater
    ip_num = len(systems)
    for x in range(ip_num):
        worker = NetWorker(queue)
        # Setting daemon to True will let the main thread exit even
        # though the workers are blocking
        worker.daemon = True
        worker.start()
    # determine systems[repeater].status
    for repeater in systems:
        # Put the tasks into the queue as a tuple
        queue.put((systems, repeater, myip))

    # Causes the main thread to wait for the queue to finish
    # processing all the tasks
    queue.join()

    # write out html
    generate_html(systems)


if __name__ == "__main__":
    import subprocess
    from time import ctime
    import httplib
    import re
    import ConfigParser
    import socket

    configfile = "gwstatus.ini"

    config = readconfigfile(configfile)

    main()
