#!env/python3
# coding: utf-8


# Import smtplib for the actual sending function
import smtplib

# Import the email modules we'll need
from email.mime.text import MIMEText

# Open a plain text file for reading.  For this example, assume that
# the text file contains only ASCII characters.
msg = MIMEText("Salut ! ceci est un test")

# me == the sender's email address
# you == the recipient's email address
msg['Subject'] = 'Test notification'
msg['From'] = 'notification@regovar.org'
msg['To'] = 'gueudelotolive@gmail.com'

# Send the message via our own SMTP server.
s = smtplib.SMTP('smtp.univ-angers.fr')
s.send_message(msg)
s.quit()