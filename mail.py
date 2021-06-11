import smtplib, config
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send(message, subject="", to="", port=config.smtp_port, host=config.smtp_host, user=config.smtp_user):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = user
    msg['To'] = to
    msg.attach(MIMEText(message, "html"))

    _DEFAULT_CIPHERS = (
'ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:ECDH+HIGH:'
'DH+HIGH:ECDH+3DES:DH+3DES:RSA+AESGCM:RSA+AES:RSA+HIGH:RSA+3DES:!aNULL:'
'!eNULL:!MD5')

    smtp_server = smtplib.SMTP(host, port=port)

# only TLSv1 or higher
    context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    context.options |= ssl.OP_NO_SSLv2
    context.options |= ssl.OP_NO_SSLv3

    context.set_ciphers(_DEFAULT_CIPHERS)
    context.set_default_verify_paths()
    context.verify_mode = ssl.CERT_NONE

    if smtp_server.starttls(context=context)[0] != 220:
        return False # cancel if connection is not encrypted
    try:
        smtp_server.sendmail(user, to, msg.as_string())
        return True, None
    except smtplib.SMTPException as e:
        return False, e


if __name__=="__main__":
    sent, error = send("<u>test</u>", "test", ["yui9911324@gmail.com"])
    if error:
        print(error)
