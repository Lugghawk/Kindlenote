#!/usr/bin/python
from getpass import getpass
import optparse
import os
import smtplib
from socket import error as sockError
import sys

### Parse command-line options

parser = optparse.OptionParser(usage='Usage: %prog [options] <files>')
parser.add_option('-c', '--convert', help='add convert tag to the subject line',
		dest='convert', default=False, action='store_true')

if not sys.argv[1:]: # No arguments provided.
	parser.print_help()
	sys.exit(2)

(opts, files) = parser.parse_args()

if not files: # No filenames provided.
	print "You must provide at least one file to send."
	sys.exit(2)

##Continue with imports
try:
	import config
except ImportError:
	print """config.py not found.

Your config file, config.py, needs to be filled in. Take config_sample.py and copy it to config.py, fill in your smtp details, and fire away."""
	sys.exit(1)

##Attachment imports##
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders


DEBUG = True # Sets our debug status to true. Will give some extra logging throughout the connection process.
################################################


################################################
##Config File Check## 


def checkConfig():
	if not (config.smtpServer and config.smtpPort and config.userName and
			config.to_addr and config.from_addr and config.maxAttachments):
		#Make sure the required items are there.
		print "There was a problem with your config. One or more of the required values are not set."
		print "Please correct your config.py file and try again"
		sys.exit(1) # Exits the program since the config file is not right.
	else:
		print "Config file has data in the required fields"
	
################################################
##Function Declarations##
def sendMail(from_addr, to_addr, mesg, smtpObject,attach=[], convertFlag = False):
	
	msg = MIMEMultipart()
	msg['From'] = from_addr
	msg['To'] = to_addr
	msg['Date'] = formatdate(localtime=True)
	
	
	subject = "Item from Kindlenote"
	if convertFlag:
		if DEBUG:
			print "Adding convert!"
		subject += " - Convert"
	msg['Subject'] = subject
	
	
	msg.attach(MIMEText("Thanks for using Kindlenote"))
	
	for files in attach:
		part = MIMEBase('application', "octet-stream")
		part.set_payload( open (files,"rb").read())
		
		#Rename the file in the attachment to .txt
		#We have to do this after we open it, it's just the name in python that we add to the header.
		#Amazon only allows certain extensions to the kindle.
		dot_idx = files.rfind(".")
		if dot_idx >= 0:
			# Remove everything from the end until (and including) the last dot
			files = files[:dot_idx]
		files += ".txt"
		
		Encoders.encode_base64(part)
		part.add_header('Content-Disposition', 'attachment; filename="'+files+'"')
		msg.attach(part)
		
	try:
		smtpObject.sendmail(from_addr, to_addr, msg.as_string())
	except smtplib.SMTPException:
		print "There was a problem sending your message"	
	else: 
		print "Message sent successfully"

	
def smtpLogin(userName, passWord, smtpObject):
	if passWord == '':
		#The password wasn't set in the config file. We need to prompt the user for it.
		passWord = getpass()
	try:
		smtpObject.login(userName, passWord)
		del(userName) # Can't be too careful.
		del(passWord)
	except smtplib.SMTPAuthenticationError:
		print "There was an error during authentication. Check your credentials in config.py"
		sys.exit(1)
	else: 
		if DEBUG:
			print "Authentication with "+config.smtpServer+" successful."
		
def checkArgs (arguments): # Checks files that are specified at command line exist. Adds all command line items to a stack so it only has to loop once.
	filesToSend = []
	for arg in arguments:
	
		if os.access(arg, os.R_OK):
			if arg not in filesToSend:
				filesToSend.append(arg)
			else:
				print "Duplicate file:", arg
		else:
			print "File", arg, "doesn't exist. Skipping."
			#filesDontExist = True #Removing since we don't need to exit, just say that we're skipping that file.
	
	if len(filesToSend) == 0:
		print "Exiting since no files listed" # Shouldn't happen, but just in case.
		sys.exit(1) # Exiting due to a parameter's files not existing.

	return filesToSend
	
	
################################################
##PROGRAM STARTS HERE##
################################################




checkConfig()
#Try to connect to our server.
try:
	if config.smtpSSL:
		server = smtplib.SMTP_SSL(config.smtpServer, config.smtpPort)
	else:
		server = smtplib.SMTP(config.smtpServer, config.smtpPort)

	server.ehlo_or_helo_if_needed()
except sockError as e:
	print e
	sys.exit(1)
except (smtplib.SMTPException,smtplib.SMTPConnectError):
	print "There was a problem connecting"
	sys.exit(1)
else:
	if DEBUG:
		print "Connection to " + config.smtpServer + " successful"

		

smtpLogin(config.userName, config.passWord, server)

# Filter out invalid files.
fileList = checkArgs (files)

# Split all the files into batches of config.maxAttachments files.
batchStarts = xrange(0, len(fileList), config.maxAttachments)
batches = [fileList[x:x+config.maxAttachments] for x in batchStarts]

for batch in batches:
	sendMail(config.from_addr,config.to_addr,'This is a test message',server, batch, opts.convert)
