#!/usr/bin/python

import email, getopt, imaplib, os, os.path, sys, tempfile, yaml

def usage(progName):
    print "Usage is\n\t%s [-c CONFFILE]" % (progName)

try:
    opts, args = getopt.getopt(sys.argv[1:], 'c:t')
except getopt.GetoptError as err:
        # print help information and exit:
        print str(err)  # will print something like "option -a not recognized"
        usage(sys.argv[0])
        sys.exit(2)

home = os.path.expanduser("~")
conffiles=["FetchAndDropMail.yml", os.path.join(home, ".FetchAndDropMail.yml"),  None]
testmode=False

for o, a in opts:
    if o == "-c":
        conffiles=[a, None]
    if o == "-t":
        testmode=True


for fname in conffiles:
    if not fname:
        print 'No configuration file found'
        exit(1)
    if os.path.isfile(fname):
        break

with open(fname, 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

destdir = cfg['dest']['dir']

class FetchEmail():

    connection = None
    error = None

    def __init__(self, mail_server, username, password, port=0, readonly=False):
        if port==0:
            port=993
        self.connection = imaplib.IMAP4_SSL(mail_server, port)

        self.connection.login(username, password)
        self.connection.select(readonly=readonly) # so we can mark mails as read
        #self.connection.select(readonly=True) # For testing

    def close_connection(self):
        """
        Close the connection to the IMAP server
        """
        self.connection.close()

    def save_attachment(self, msg, download_folder="/tmp"):
        """
        Given a message, save its attachments to the specified
        download folder (default is /tmp)

        return: file path to attachment
        """
        att_path = "No attachment found."
        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue

            filename = part.get_filename()
            att_path = os.path.join(download_folder, filename)

            if not os.path.isfile(att_path):
                fp = open(att_path, 'wb')
                fp.write(part.get_payload(decode=True))
                fp.close()
        return att_path

    def fetch_unread_messages(self):
        """
        Retrieve unread messages
        """
        emails = []
        (result, messages) = self.connection.search(None, 'UnSeen')
        if result == "OK":
            for message in messages[0].split(' '):
                try: 
                    ret, data = self.connection.fetch(message,'(RFC822)')
                except:
                    self.close_connection()
                    raise Exception("No new emails to read.")


                #msg = email.message_from_bytes(data[0][1])
                msg = email.message_from_string(data[0][1])
                if isinstance(msg, str) == False:
                    emails.append(msg)
                response, data = self.connection.store(message, '+FLAGS','\\Seen')

            return emails

        self.error = "Failed to retreive emails."
        return emails

    def parse_email_address(self, email_address):
        """
        Helper function to parse out the email address from the message

        return: tuple (name, address). Eg. ('John Doe', 'jdoe@example.com')
        """
        return email.utils.parseaddr(email_address)

f=FetchEmail(
    cfg['imap']['host'],
    cfg['imap']['username'],
    cfg['imap']['password'],
    993,
    testmode
    )
try:
    emails=f.fetch_unread_messages()
except Exception as e:
    exit()
dirpath = tempfile.mkdtemp()

nAttach=[]
dropped=[]
for mail in emails:
    f.save_attachment(mail, dirpath)
    onlyfiles = [f for f in os.listdir(dirpath) if os.path.isfile(os.path.join(dirpath, f))]
    for f in onlyfiles:
        fparts = os.path.splitext(f)
        extension=fparts[1][1:]
        prefix = fparts[0]
        if extension in ('pdf'):
            otarget=os.path.join(destdir,prefix)
            src=os.path.join(dirpath,f)
            ntarget=otarget+'.'+extension
            n=0
            while os.path.exists(ntarget):
                print 'File already exists' + ntarget
                n+=1
                ntarget=otarget+'-'+str(n)+'.'+extension
            else:
                os.rename(src,ntarget)
                nAttach.append(ntarget)
        else:
            os.unlink(f)
            droppeed.append(f)
print nAttach
print dropped
os.rmdir(dirpath)
