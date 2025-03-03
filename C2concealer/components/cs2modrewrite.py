#!/usr/bin/env python

## Title:       cs2modrewrite.py
## Author:      Joe Vest, Andrew Chiles

import sys
import re

description = '''
Python 3.0+
Converts Cobalt Strike (<=4.0) profiles to Apache mod_rewrite .htaccess file format by using the User-Agent and URI Endpoint to create rewrite rules.
Make sure the profile passes a c2lint check before running this script.
Note: Additional User-Agent specifications within http-get or http-post client blocks are not accounted for by this script
'''

def cs2modrewrite(inputfile, c2server, redirect, outfile):

    # Make sure we were provided with vaild URLs
    # https://stackoverflow.com/questions/7160737/python-how-to-validate-a-url-in-python-malformed-or-not
    regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    if re.match(regex, c2server) is None:
        print("[!] c2server is malformed. Are you sure {} is a valid URL?".format(c2server),file=sys.stderr)
        sys.exit(1)

    if re.match(regex, redirect) is None:
        print("[!] redirect is malformed. Are you sure {} is a valid URL?".format(redirect),file=sys.stderr)
        sys.exit(1)

    profile = open(inputfile, "r")
    contents = profile.read()

    # Strip all single line comments (#COMMENT\n) from profile before searching so it doesn't break our crappy parsing
    contents = re.sub(re.compile("#.*?\n" ) ,"" ,contents)

    # Search Strings
    ua_string  = "set useragent"
    set_uri    = r"set uri.*\"(.*?)\"\;"

    # Errors
    errorfound = False
    errors = "\n##########\n[!] ERRORS\n"

    # Get UserAgent
    if contents.find(ua_string) == -1:
        ua = ""
        errors += "[!] User-Agent Not Found\n"
        errorfound = True
    else:
        ua_start = contents.find(ua_string) + len(ua_string)
        ua_end   = contents.find("\n",ua_start)
        ua       = contents[ua_start:ua_end].strip()[1:-2]

    # Get all profile URIs based on our regex
    if len(re.findall(set_uri,contents)) == 0:
        uris = ""
        errors += "[!] No URIs found\n"
        errorfound = True
    else:
        uris = re.findall(set_uri,contents)
        # Split any uri specifications to handle cases where multiple URIs are separated by whitespace
        # i.e. set uri "/path/1 /path/2"
        split_uris = []
        for uri in uris:
            for i in uri.split():
                split_uris.append(i)
        # Remove any duplicate URIs
        uris = list(set(split_uris))

    # Create UA in modrewrite syntax. No regex needed in UA string matching, but () characters must be escaped
    ua_string = ua.replace('(','\(').replace(')','\)')

    # Create URI string in modrewrite syntax. "*" are needed in regex to support GET and uri-append parameters on the URI
    uris_string = ".*|".join(uris) + ".*"

    htaccess_template = '''
    ########################################
    ## .htaccess START
    RewriteEngine On
    
    ## (Optional)
    ## Scripted Web Delivery
    ## Uncomment and adjust as needed
    #RewriteCond %{{REQUEST_URI}} ^/css/style1.css?$
    #RewriteCond %{{HTTP_USER_AGENT}} ^$
    #RewriteRule ^.*$ "http://TEAMSERVER%{{REQUEST_URI}}" [P,L]
    
    ## Default Beacon Staging Support (/1234)
    RewriteCond %{{REQUEST_METHOD}} GET [NC]
    RewriteCond %{{REQUEST_URI}} ^/..../?$
    RewriteCond %{{HTTP_USER_AGENT}} "{ua}"
    RewriteRule ^.*$ "{c2server}%{{REQUEST_URI}}" [P,L]
    
    ## C2 Traffic (HTTP-GET, HTTP-POST, HTTP-STAGER URIs)
    ## Logic: If a requested URI AND the User-Agent matches, proxy the connection to the Teamserver
    ## Consider adding other HTTP checks to fine tune the check.  (HTTP Cookie, HTTP Referer, HTTP Query String, etc)
    ## Refer to http://httpd.apache.org/docs/current/mod/mod_rewrite.html
    ## Only allow GET and POST methods to pass to the C2 server
    RewriteCond %{{REQUEST_METHOD}} ^(GET|POST) [NC]
    ## Profile URIs
    RewriteCond %{{REQUEST_URI}} ^({uris})$
    ## Profile UserAgent
    RewriteCond %{{HTTP_USER_AGENT}} "{ua}"
    RewriteRule ^.*$ "{c2server}%{{REQUEST_URI}}" [P,L]
    
    ## Redirect all other traffic here
    RewriteRule ^.*$ {redirect}/? [L,R=302]
    
    ## .htaccess END
    ########################################
    '''
    print("#### Save the following as .htaccess in the root web directory")
    print("## Profile User-Agent Found:")
    print("# {}".format(ua))
    print("## Profile URIS Found ({}):".format(str(len(uris))))
    for uri in uris:
        print("# {}".format(uri))

    htaccess = htaccess_template.format(uris=uris_string, ua=ua_string, c2server=c2server, redirect=redirect)
    if outfile:
        with open(outfile, 'w') as out_file:
            out_file.write(htaccess)
    else:
        print(htaccess)


    # Print Errors Found
    if errorfound:
        print(errors, file=sys.stderr)


