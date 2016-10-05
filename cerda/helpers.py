import argparse
import getpass
import logging
import os
import re
import smtplib

from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

import dropbox

from cerda.errors import CerdaError

logger = logging.getLogger(__name__)

def dropbox_setup():
    token_path = os.path.join(os.path.expanduser(os.path.sep.join(['~', '.cerda'])), 'dbox_token.txt')
    logger.debug("Token location: %s", token_path)

    APP_KEY = 'gpf11zjrtp5od4x'
    APP_SECRET = 'cyk4k6zgmraajy7'

    logger.debug("Does token file exist on disk?")

    if os.path.isfile(token_path):
        logger.debug("YES! Opening token file...")

        token_file = open(token_path)
        access_token = token_file.read()
        token_file.close()

    else:
        logger.info((
            "You will have to give me permissions to upload stuff to your"
            "Dropbox account. In order for me to do that you will need to"
            "authorize Cerda in your account, don't worry it's just a one time"
            "thing.")
        )

        flow = dropbox.client.DropboxOAuth2FlowNoRedirect(APP_KEY, APP_SECRET)
        authorize_url = flow.start()

        logger.info("1. Go to: %s", authorize_url)
        logger.info("2. Click 'Allow' (you might have to log in first).")
        logger.info("3. Copy the authorization code.")

        code = raw_input("Enter the authorization code here: ").strip()

        access_token, user_id = flow.finish(code)

        logger.debug("Access token is... %s", access_token)

        logger.debug("Writing access token's key and secret to file...")

        token_folder = os.path.dirname(token_path)

        if not os.path.exists(token_folder):
            os.makedirs(token_folder)        

        token_file = open(token_path, 'w')
        token_file.write(access_token)
        token_file.close()

    client = dropbox.client.DropboxClient(access_token)
    logger.info("Yay! %s, I just hooked to your Dropbox account!", client.account_info()['display_name'])
    return client

def email_sender(email_address, processed_items):
    logger.debug("Preparing email for %s", email_address)
    logger.debug("Processed items are %s", processed_items)
    
    fromaddr = "cerda.ncca@gmail.com"
    toaddr = email_address

    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "cerda: Report"

    body = "Renders are finished!\n%s" % processed_items

    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, "NCCA2016cerda")
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()

def get_abs_form_rel(rel_dir, username):
    return os.path.join(
        '/',
        os.path.join(
            'home',
            username,
            *rel_dir.split('/')
        )
    )

p_des = "Process credentials and paths for farm watcher"
s_des = "Remote location path (relative to home) where the frames get generated."
t_des = "Destination location path where you would like the frames to get sent to."
d_des = "Will send the files to the root path of your dropbox account."
m_des = "Email address to send notification to after -c frames have been rendered."
c_des = "At this numer of frames, send an email to the address specified with -m flag."
e_des = "How often to check for frames dropped (in seconds)"

def parse_args(args):
    parser = argparse.ArgumentParser(description=p_des)
    parser.add_argument('-s', '--source', help=s_des, required=True)
    parser.add_argument('-t', '--target', help=t_des, required=True)
    parser.add_argument('-dbox', '--dropbox', help=d_des, action='store_true')
    parser.add_argument('-m', '--email', help=m_des)
    parser.add_argument('-c', '--count', help=c_des, type=int)
    parser.add_argument('-e', '--every', help=e_des, type=int, default=5)
    args = parser.parse_args(args)

    if args.email or args.count:
        if not (args.email and args.count is not None):
            logger.error("-c (--count) and -m (--mail) both need to be passed, not just one.")
            raise CerdaError("gdg")

        else:
            logger.debug("Email passed in is: %s", args.email)
            logger.debug("Frame count for sending email is: %s", args.count)
            EMAIL_REGEX = re.compile(r'[^@]+@[^@]+\.[^@]+')
            if not EMAIL_REGEX.match(args.email):
                raise CerdaError("You entered an invalid email. Typo maybe?")

    # Validation on -s / --source to be implemented

    # validation on -t / --target to be implemented

    # Validation on -e / --every to be implemented

    # Validation on -c / --count
    if args.count < 1:
        raise CerdaError("You want to be sent an email after %s frames have been rendered? That does not make any sense..." % args.count)

    # Dropbox handling
    client = None
    if args.dropbox:
        client = dropbox_setup()

    user = getpass.getuser()
    password = getpass.getpass("Password for %s: " % user)

    return (user, password, args.source, args.target, args.email, int(args.count), client, args.every)