'''

##########################################
Data set containing common dns subdomains. 
##########################################

'''
#Customize this#
subdomains = ['ns0','ns1','ns2']

beacon = ['doc.bc.']                         #DNS subhost prefix used for beaconing requests

get_a = ['doc.1a.']                          #DNS subhost prefix used for A record requests

get_aaaa = ['doc.4a.']                       #DNS subhost prefix used for AAAA record requests

get_txt = ['doc.tx.']                        #DNS subhost prefix used for TXT record requests

put_metadata = ['doc.md.']                   #DNS subhost prefix used for metadata requests

put_output = ['doc.po.']                     #DNS subhost prefix used for output requests

ns_response = ['drop','idle','zero']         #How to process NS Record requests. "drop" does not respond to the request (default),
                                             #"idle" responds with A record for IP address from "dns_idle",
                                             #"zero" responds with A record for 0.0.0.0
