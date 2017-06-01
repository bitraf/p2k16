import smtplib
from email.mime.text import MIMEText

from p2k16 import app

def send(email=None, subject=None, message=None):
    """
    Sends a email using mail server in MAIL_HOST config variable and MAIL_FROM as sender
    :param email: Destination email adress
    :param subject: Email subject
    :param message: Email message
    :return: 
    """
    msg = MIMEText(message)

    msg['Subject'] = subject
    msg['From'] = app.config['MAIL_FROM']
    msg['To'] = email

    # Send the message via our own SMTP server.
    s = smtplib.SMTP(app.config['MAIL_HOST'],local_hostname="p2k12.bitraf.no")
    s.send_message(msg)
    s.quit()


def _test_config():
    import sys
    fail = False
    if 'MAIL_HOST' not in app.config.keys():
        print("MAIL_HOST config property not found, Test failed.")
        fail = True
    if 'MAIL_FROM' not in app.config.keys():
        print("MAIL_FROM property not found, Test failed.")
        fail = True

    if fail is True:
        sys.exit(2)
    else:
        print("All tests are OK!")


def _test_mail(email):
    message = "This is a test. If you get this message, email from p2k16 mail system is ok"
    subject = "Test email from p2k16"
    send(email=email, subject=subject, message=message)


if __name__ == '__main__':
    import sys
    if len(sys.argv) == 2:
        argument = sys.argv[1]
        if '@' in argument:
            print("Found a @ in argument, trying to send a test email to the address {}.".format(argument))
            _test_mail(argument)
        else:
            print("To send a test email, add a valid email as argument to the script {}".format(sys.argv[0]))
    else:
        _test_config()


