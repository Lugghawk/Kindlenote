import smtplib
import sys
import os

##Check for --help etc
##Need to do this first since they may --help without moving over their config. If they do, we shouldn't bombard them with errors about a missing config, since we don't really need it to show them the help.
sys.argv.pop(0) # Get rid of the script name, we don't need it.
#Check for 'Convert' flag.
if sys.argv[0] == '-c':
	#Convert!
	if DEBUG:
		print "Convert flag found!"
	convert = True #We pass this to our sendMail function so that our subject line contains the word Convert.
	sys.argv.pop(0)
elif sys.argv[0] == '--help':
	print """
	Usage: 
	
	kindlenote.py [-c]  [--help] <filename1> <filename2> ...
	
	-c: Add convert tag to the subject line. 
	
	--help: Show this screen
	
	<filename#>: Include a file in your next send from kindlenote.
	
	Your config file, config.py, needs to be filled in. Take config_sample.py and copy it to config.py, fill in your smtp details, and fire away.
	"""
	sys.exit(0)

##Continue with imports
try:
	import config
except ImportError:
	print "config.py not found. Please check config_sample.py and fill in your details"
	sys.exit(0)

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
	if config.smtpServer == '' or config.userName == '' or config.passWord == '' or config.to_addr == '' or config.from_addr == '':
		print "There was a problem with your config. One or more of the required values are not set."
		config.configFile = False

	if config.configFile:
		print "Config file has data in the required fields"
	else:
		print "Please correct your config.py file and try again"
		sys.exit(0) # Exits the program since the config file is not right.
################################################
##Function Declarations##
def sendMail(from_addr, to_addr, mesg, smtpObject,attach=[], convertFlag = False):
	
	msg = MIMEMultipart()
	msg['From'] = from_addr
	msg['To'] = to_addr
	msg['Date'] = formatdate(localtime=True)
	
	
	if convertFlag:
		if DEBUG:
			print "Adding convert!"
		msg['Subject'] = "Item from Kindlenote - Convert"
	else:
		msg['Subject'] = "Item from Kindlenote"
	
	
	msg.attach(MIMEText("Thanks for using Kindlenote"))
	
	for files in attach:
		part = MIMEBase('application', "octet-stream")
		part.set_payload( open (files,"rb").read())
		
		#Rename the file in the attachment to .txt
		#We have to do this after we open it, it's just the name in python that we add to the header.
		#Amazon only allows certain extensions to the kindle.
		files = files[:-2]
		files = files + "txt"
		
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
	try:
		smtpObject.login(userName, passWord)
		del(userName) # Can't be too careful.
		del(passWord)
	except smtplib.SMTPAuthenticationError:
		print "There was an error during authentication. Check your credentials in config.py"
	else: 
		if DEBUG:
			print "Authentication with "+config.smtpServer+" successful."
		
def checkArgs (arguments): # Checks files that are specified at command line exist. Adds all command line items to a stack so it only has to loop once.
	filesToSend = []
	filesDontExist = False
	for arg in arguments:
		try:
			open(arg,"r")
		except IOError:
			print "File " + arg +" doesn't exist"
			filesDontExist = True
		filesToSend.append (arg)
	
	if filesDontExist:
		print "Exiting"
		sys.exit(0) # Exiting due to a parameter's files not existing.
	
	return filesToSend
	
	
################################################
##PROGRAM STARTS HERE##
################################################




checkConfig()
#Try to connect to our server.
try:
	server = smtplib.SMTP_SSL(config.smtpServer,465) # Use SSL by default atm.
	server.ehlo_or_helo_if_needed()
except (smtplib.SMTPException,smtplib.SMTPConnectError):
	"There was a problem connecting"
else:
	if DEBUG:
		print "Connection to " + config.smtpServer + " successful"
	
smtpLogin(config.userName, config.passWord, server)

#Count the files on command line.
	
fileList = checkArgs (sys.argv)
	
sendMail(config.from_addr,config.to_addr,'This is a test message',server,fileList, convert)
