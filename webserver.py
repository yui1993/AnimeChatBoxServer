import cherrypy, config

def _get_verify_html(key, user):
    key = str(key)
    user = str(user)
    f = open("web/verify.html", "r")
    cts = f.read().replace("{{key}}", key).replace("{{user}}", user)
    f.close()
    return cts

def _get_html(key, user):
    key = str(key)
    user = str(user)
    f = open("web/forget.html", "r")
    cts = f.read().replace("{{key}}", key).replace("{{user}}", user)
    f.close()
    return cts

def change_to_user():
    try:
        if os.name == 'posix':
 
            pw = pwd.getpwnam("chat")
            uid = pw.pw_uid
            os.setuid(uid)
            ##--- create file as test of permissions
    except Exception as e:
        print(e) # Error


class RootServer:
    @cherrypy.expose
    def index(self, **keywords):
        change_to_user()
        return _get_html(cherrypy.request.params.get("key"), cherrypy.request.params.get("user"))
    
    @cherrypy.expose("/verify")
    def verify(self, **keywords):
        change_to_user()
        return _get_verify_html(cherrypy.request.params.get("key"), cherrypy.request.params.get("user"))

if __name__ == '__main__':
    if config.use_ssl:
        server_config={
            'server.socket_host': '0.0.0.0',
            'server.socket_port': config.webserver_port,

            'server.ssl_module': 'builtin',
            'server.ssl_private_key': config.ssl_key,
            'server.ssl_certificate': config.ssl_cert
        }
    else:
        server_config={
            'server.socket_host': '0.0.0.0',
            'server.socket_port': config.webserver_port
        }

    cherrypy.config.update(server_config)
    cherrypy.quickstart(RootServer())