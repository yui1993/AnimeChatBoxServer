use_ssl=False # use to encrypt webserver and websocket
ssl_key=None # key file path
ssl_cert=None # cert file path
port=80 # websocket port
smtp_port = 25 # email port
smtp_host = "localhost" # email host
smtp_user = "no-reply@localhost" # email user that user sees that emails them
domain="localhost" # used to point to webserver in emails
webserver_port=4441 # webserver port
path_to_key=".db.k" # database encryption key
passwordsalt = "!@#$%^&*()_++_)(*&^%$#@!1234567890-=yguujop;l;k;kllkjftrtwercgvbnm,m.,lklkhhg#$%^&&*&*^^$$%##@$!$#^&O(P)_++_" # for encrypting passwords
dbname="db.encrypted" # file for the encrypted json
setup_db=True # set this to False after first run
allowed_tags = ["a", "li", "ul", "img", "em", "code", "b", "u", "i", "p"] # allowed html tags
allowed_attrs = {
    "*": ["style", "src", "align", "height", "width", "href", "target", "alt"] # allowed attributes
}
if use_ssl:
    protocol = "https"
    websocket_protocol = "wss"
else:
    protocol = "http"
    websocket_protocol = "ws"
