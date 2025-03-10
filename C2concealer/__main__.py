#!/usr/bin/env python3

from .profile import Profile
import argparse
import sys
import os
import fnmatch
import string
from C2concealer.helpers import chooseSSL, _debug_generateOneProfile, find, variantCountSelection


def main():

	'''

	Driver function for the C2concealer module.

	The main function first instantiates the Profile class and then
	calls the randomizer() method to provide the profile instance
	with a random set of Indicators of Compromise. Then,
	buildMainProfile() method is called to construct a long string comprising
	the entire profile with correct indentation (ex: \n \t). Next, variants are built
	according to the number of variants passed in on the command line. The long string
	is outputted to a file by calling the outputProfile() method. Then the c2LintCheck()
	function runs CobaltStrike's c2lint application against the newly
	generated profile to validate it. If it's a valid profile, the IoC preview generated
	by c2lint is outputted to stdout along with a summary. If the profile fails validation,
	then the profile is removed from disk and the process is repeated (max 10 times). If after
	10 attempts no profile is valid, the program will exit. This shouldn't happen often, but if it doesn
	just run it again.

	Output: a validated C2 malleable profile

	Note: In the recent update of c2lint, the console output (c2lint results) for the variants
	are in alphabetical order. As a result, if you select 10 variants, named variant_1 - variant_10,
	the last variant in the console output will be variant_9, but if you scroll up you'll see
	variant_10 right after variant_1. No impact on performance, but during testing I noticed this
	and wanted to document in case anyone else is confused.

	'''

	parser = argparse.ArgumentParser(
	add_help=False, description="C2concealer builds C2 malleable profiles\
	filled with randomized data for use with Cobalt Strike.")
	parser.add_argument('-h', '-?', '--h', '-help', '--help', action="store_true",
	help=argparse.SUPPRESS)
	parser.add_argument('--variants', type=int, help="Enter the count of http client/server \
		variants to create.")
	parser.add_argument('--hostname', type=str, help="Enter the hostname used for domain fronting or redirection")
	parser.add_argument('--rewrite', type=str, help="If using a redirector, this will generate the rewrite rules \
													options are either 'apache' or 'nginx'")
	#parser.add_argument('--debug', action='store_true')

	args = parser.parse_args()
	if args.h:
		parser.print_help()
		sys.exit()

	##Check variant is an integer
	if args.variants:
		try:
			variant_count = int(args.variants)
		except:
			print("[x] You must input an integer as the variant value. 0-10 are good values.")
			sys.exit()
	else:
		variant_count = 0

	##Check/clean hostname
	if args.hostname:
		hostname = args.hostname
		if "http://" in hostname:
			hostname = hostname.replace("http://","")
		if "https://" in hostname:
			hostname = hostname.replace("https://","")
	else:
		hostname = None

	##Check rewrite
	if args.rewrite:
		rewrite = args.rewrite
		if "apache" in rewrite:
			rewrite = "cs2modrewrite"
		if "nginx" in rewrite:
			rewrite = "cs2nginx"
	else:
		rewrite = None

	if(os.path.exists('/usr/share/cobaltstrike/c2lint')):
		path = '/usr/share/cobaltstrike/c2lint'
		print("[i] Found c2lint in the /usr/share/cobaltstrike directory.\n")
	else:
		print("[i] Searching for the c2lint tool on your system (part of Cobalt Strike). Might take 10-20 seconds.")
		paths = find('c2lint','/')
		if(paths):
			path = paths[0]
			print("[i] Found c2lint in the {} directory.\n".format(path))
		else:
			print("[-] Can't find cobaltstrike's c2lint profile validator.")
			print("[!] Please install cobaltstrike's c2lint tool.\n")
			sys.exit()

	ssl_dict = chooseSSL()

	#if args.debug:
	#	_debug_generateOneProfile(ssl_dict, path)
	#else:
	print("[i] Building random C2 malleable profile with " + str(variant_count) + " variants.")
	retryCount = 0
	while(retryCount < 10):
		profile = Profile(ssl_dict, hostname=hostname)
		profile.randomizer()
		profile.consistencyCheck()
		profile.buildMainProfile()
		for i in range(variant_count):
			varname = "variant_" + str(i+1)
			variant = Profile(ssl_dict, varname, hostname)
			variant.randomizer()
			variant.consistencyCheck()
			variant.buildVariant()
			profile.profileString += variant.profileString
		profile.outputProfile()
		passed, lintResults = profile.c2LintCheck(path)
		if passed:
			for line in lintResults:
				if not any(w in line for w in ['[+]','[-]','[!]']):
					print(line.rstrip())
			print('############################################################')
			print("# Profile successfully passed c2lintcheck                  #")
			print('# Profile Name: ' + profile.globalOptions.sample_name + ".profile" + 27*" " + "#")
			print("# Generated by FortyNorthSecurity's C2concealer tool.      #")
			print('############################################################')

			if args.rewrite is not None:
				profile.create_rewrite(rewrite)
			sys.exit()
		else:
			if "Please run the 'update' program " in lintResults:
				print("[x] You need to run the 'update' program from within CobaltStrike before c2lint will run.")
				sys.exit()
			retryCount+=1
#			os.remove((os.getcwd() + '/C2concealer/profiles/' + profile.globalOptions.sample_name + '.profile'))

			print("[-] Attempted to create {} profiles. c2lint check failed.".format(str(variant_count)))
			print("[i] If you selected a large amount of variants, please retry again.")
			print("[x] Exiting program.")
			sys.exit()


if __name__ == '__main__':
	main()
