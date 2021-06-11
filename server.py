import util, user, config, ssl, json, time, sys, os, pwd, mail
from autobahn.twisted.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory, \
    listenWS
from twisted.internet import reactor, ssl
from twisted.web.server import Site
from twisted.web.static import File
from autobahn.twisted.resource import WebSocketResource
from twisted.python import log
from twisted.internet import reactor
from objectify import Objectify
from termcolor import colored
from database import Database
from room import Room

class WebSocketServer(WebSocketServerProtocol):
    __ran = False # not sure how many times class is initalized
    db = Database()

    def init(self):
        if not self.__ran:
            for ro in self.db.getAllRooms():
                Room(ro).set()
            
            
        WebSocketServer.__ran = True

    def onConnect(self, request):
        self.init()
        print(request.peer)
        self.id = util.generate_id()
        self.ip = request.peer.split(":")[1]
        self.uid = util.generate_uid(self.ip)
        self.user = user.User(self.id, self.ip, self)
        self.user.set()
        msg = colored(self.ip , "blue") + " " + colored("connected at ", "yellow") + colored(time.ctime(), "white", attrs=["underline"])
        print(msg)
    
    def onMessage(self, message, isBinary):
        try:
            j = json.loads(message)
            j = Objectify(j)
        except:
            j=Objectify()
        try:
            if j.get("login", True):
                name = j.user
                password = j.password
                check = self.db.check(name, password)
                if check:
                    if self.db.getUser(name).verified:
                        self.user.setName(name)
                        self.user.setLoggedIn(True)
                        self.user.write(verified=1, login=1, message="Success")
                    else:
                        self.user.write(verified=0, login=0, message="You Must verify email before logging in")
                else:
                    self.user.write(login=0, message="Incorrect user or password")
            
            elif j.get("join", True):
                if self.user.logged_in:
                    name = j.room.lower()
                    if self.db.getRoom(name.lower()):
                        self.user.setRoom(name)
                        room = Room(name.lower()).get()
                        added, message = room.add(self.user)
                        mods = self.db.getMods(name.lower())
                        if self.user.name in mods:
                            self.user.setMod(True)
                        owner = mods[-1]['owner']
                        if self.user.name == owner.lower():
                            self.user.setOwner(True)
                        if added:
                            self.user.write(joined=1, message=message)
                        else:
                            self.user.write(joined=0, message=message)
                    else:
                        self.user.write(joined=0, message=f"{name.lower()} doesn't exist")
                else:
                    self.user.write(joined=0, message="Not logged in")

            elif j.get("create", True):
                room = self.user.room
                clean = util.isAllowed(room)
                if user.logged_in:
                    if clean:
                        title = util.filter(j.title)
                        description = util.filter(j.description)
                        added = self.db.addRoom(room, user.name, title=title, description=description)
                        if added:
                            self.user.write(created=1, message=f"Created {room}")
                        else:
                            self.user.write(created=0, message=f"{room} already exists")
                    else:
                        self.user.write(created=0, message=f"{room} has invalid charactors or is to small and/or big")
                else:
                    self.user.write(created=0, message="Not logged in")

            elif j.get("mod", True):
                if j.get("mode") == "add":
                    if self.getRoom(self.user.room):
                        if j.target not in self.db.getMods(self.user.room):
                            if self.user.owner:
                                mod = self.db.addMod(self.user.room, self.user.name.lower(), j.target)
                                if mod:
                                    Room(self.user.room).get().write(modded=1, user=j.target, time=time.time(), message=f"modded {j.target}", room=self.user.room)
                                else:
                                    self.user.write(modded=0, message="Not owner", room=self.user.room)
                elif j.get("mode") == "remove":
                    if self.getRoom(self.user.room):
                        if j.target not in self.db.getMods(self.user.room):
                            if self.user.owner:
                                mod = self.db.removeMod(self.user.room, self.user.name.lower(), j.target)
                                if mod:
                                    Room(self.user.room).get().write(demodded=1, user=j.target, time=time.time(), message=f"modded {j.target}", room=self.user.room)
                                else:
                                    self.user.write(demodded=0, message="Not owner", room=self.user.room)
                elif j.get("mode") == "list":
                    if self.getRoom(j.room):
                        self.user.write(mods=self.db.getMods(self.user.room), room=j.room)
            
            elif j.get("ban", True):
                users = self.user.users.values()
                if self.getRoom(self.user.room):
                    if self.user.mod or self.user.owner:
                        self.db.addBan(self.user.room, self.user.name, j.target.lower(), j.uid)
                        for user in users:
                            if user.mod or user.owner:
                                if user.room == self.user.room:
                                    user.write(ban=1, target=j.target, by=self.user.name, time=time.time(), room=self.user.room, message="Banned")
            elif j.get("unban", True):
                users = self.user.users.values()
                if self.getRoom(self.user.room):
                    if self.user.mod or self.user.owner:
                        self.db.removeBan(self.user.room, j.target.lower(), j.uid)
                        for user in users:
                            if user.mod or user.owner:
                                if user.room == self.user.room:
                                    user.write(unban=1, target=j.target, by=self.user.name, time=time.time(), room=self.user.room, message="Unbanned")
            elif j.get("message", True):
                if self.db.getRoom(self.user.room):
                    if self.user.logged_in:
                        if not self.db.isBanned(self.user.room, self.user.name, self.user.uid):
                            mid = util.generate_id()
                            self.db.addMessage(self.user.room, self.user.name, self.user.ip, self.user.uid, util.filter(j.body), mid)
                            message = {
                                "msg": 1,
                                "room": self.user.room,
                                "user": self.user.name,
                                "uid": self.user.uid,
                                "body": util.filter(j.body),
                                "mid": mid,
                                "time": time.time()

                            }
                            room.Room(self.user.room).get().write(**message)
                        else:
                            self.user.write(banned=1, room=self.user.room, message="You are banned")
                    else:
                        self.user.write(msg=0, message="Not logged in")
            
            elif j.get("delete", True):
                if self.db.getRoom(self.user.room):
                    if self.user.mod or self.user.owner:
                        deleted, error = self.db.removeMessageById(self.user.room, j.mid)
                        if deleted:
                            room.Room(j.name).get().write(deleted=1, room=self.user.room, mid=j.mid, message="Deleted")
                    else:
                        self.user.write(deleted=0, message="Not mod or owner")

            elif j.get("deleteuser", True):
                if self.user.mod or self.user.owner:
                    deleted = self.db.removeMessagesByUser(self.user.room, j.user)
                    room.Room(self.user.room).get().write(deleteuser=1, user=j.user, room=self.user.room, deleted=deleted, count=deleted, message="Deleted")
                else:
                    self.user.write(deleteuser=0, message="Not mod or owner")
            
            elif j.get("description", True):
                if self.user.owner:
                    description = util.filter(j.description)
                    self.db.setRoomDescription(self.user.room, description)
                    Room(self.user.room).get().write(setdescription=1, description=description, message="Set")
                else:
                    self.user.write(setdescription=0, message="Not mod or owner")
                    
            
            elif j.get("title", True):
                if self.user.owner:
                    title = util.filter(j.title)
                    self.db.setRoomTitle(self.user.room, title)
                    Room(self.user.room).get().write(settitle=0, title=title, message="Set")
                else:
                    self.user.write(settitle=0, message="Not owner")
            
            elif j.get("register", True):
                user = j.name
                email = j.email
                password = j.password
                if util.isAllowed(user):
                    register = self.db.addUser(user, email, password)
                    if register:
                        key = self.db.addVerifyKey(user)
                        sent, error = mail.send(message=f" Click <a href='{config.protocol}://{config.domain}:{config.webserver_port}/verify/?key={key}&user={user}' target='_blank'>Here</a> to verify email or copy {config.protocol}://{config.domain}:{config.webserver_port}/verify/?key={key}&user={user} and paste in browser", subject=f"Verify Email - {user}", to=email)
                        if sent:
                            self.user.write(registered=1, message="You are now registered. Please verify email before logging in. Check email for more details try spam/junk folder")
                    else:
                        self.user.write(registered=0, message=f"{user} already taken")
                else:
                    self.user.write(registered=0, message=f"{user} invalid charactors or to small/big or {user} may contain banned words")
            elif j.get("forgotpassword", True):
                email = j.email
                name = j.name
                user = self.db.getUser(name)
                if user.email == email:
                    key = self.db.setForgotPasswordKey(name)
                    sent, error = mail.send(message=f" click <a href='{config.protocol}://{config.domain}:{config.webserver_port}/?key={key}&user={name}' target='_blank'>{key}</a> to reset password or copy {config.protocol}://{config.domain}:{config.webserver_port}/?key={key}&user={name} and paste in browser", subject=f"Forgot Password - {name}", to=email)
                    if sent:
                        self.user.write(sent=1, message="Check email maybe spam folder")
                    elif error:
                        self.user.write(sent=0, message=f"Couldn't send to email on file (error: {error})")
                else:
                    self.user.write(sent=0, message="Email doesn't match email on file with that user")
            elif j.get("checkKey", True):
                key = j.key
                name = j.name
                check = self.db.checkForgotKey(name, key)
                if check:
                    self.user.write(checked=1)
                    self
                else:
                    self.user.write(checked=0)
            elif j.get("setpassword", True):
                key = j.key
                name = j.name
                password = j.password
                set = self.db.setPassword(name, password, key)
                if set:
                    self.user.write(forgot=1)
                    self.db.removeKey(key)
            elif j.get("verify", True):
                name = j.get("name", True)
                key = j.get("key", True)
                verify = self.db.checkVerify(name, key)
                if verify:
                    self.db.setVerified(name)
                    self.db.removeVerifyKey(name, key)
                    self.user.write(verified=1)
                else:
                    self.user.write(verified=0)

            elif j.get("logout", True):
                if self.user.logged_in:
                    room = self.user.room
                    user = self.user
                    self.user.setLoggedIn(False)
                    self.user.setMod(False)
                    self.user.setOwner(False)
                    self.user.setName("anon_"+self.user.uid[0:10])
                    Room(room).get().remove(self.user.uid)

            elif j.get("removeroom", True):
                if self.user.owner:
                    name = self.user.room
                    self.db.removeRoom(self.user.room, self.user.name)
                    Room(self.user.room).get().write(removed=1, message=f"{self.user.name} deleted this room")
                    users = Room(self.user.room).get().users.values()
                    for user in users:
                        Room(self.user.room).get().remove(user.uid, "user")
                    del Room.rooms[name]
                else:
                    self.user.write(removed=0, message="Not owner")





        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            line=exc_tb.tb_lineno
            msg=colored("ERROR: ", "red", attrs=["underline"]) +\
             colored(str(exc_type) + " ", "green") + colored(fname + " ", "white", attrs=["underline"]) +\
             colored(f"at line {line} ", "yellow") +\
             colored(str(e), "red", attrs=["underline"])
            print(msg)   

    def onClose(self, clean, code, reason):
        try:
            roomname = self.user.room
            msg = colored(f"{self.ip}({colored(self.user.name, 'green')}) room({colored(str(roomname), 'green')})", "magenta") + " - " +\
                colored(time.ctime(), "white", attrs=["underline"])
            if roomname:
                ro = Room(roomname)
                room = ro.get(roomname)
                if room:
                    ro.remove(self.user.uid, "user")
                    del self.user
                    del self.ip
                    del self.id
            else:
                del self.user
                del self.ip
                del self.id
        
            print(msg)
        except:
            pass


def change_to_user():
        try:
           if os.name == 'posix':
 
               pw = pwd.getpwnam("chat")
               uid = pw.pw_uid
               os.setuid(uid)
 
               ##--- create file as test of permissions
        except Exception as e:
           print(e) # Error


class WebSocketServerFact(WebSocketServerFactory):
    def __init__(self, uri):
        WebSocketServerFactory.__init__(self, uri)
def main():
    if config.use_ssl:
        log.startLogging(sys.stdout)

        contextFactory = ssl.DefaultOpenSSLContextFactory(config.ssl_key, config.ssl_cert)

        factory = WebSocketServerFact(f"wss://0.0.0.0:{config.port}")

        factory.protocol = WebSocketServer
        listenWS(factory, contextFactory)

        resource = WebSocketResource(factory)

        root = File(".")
        # note that Twisted uses bytes for URLs, which mostly affects Python3
        root.putChild(b"ws", resource)
        site = Site(root)

        reactor.listenSSL(config.port + 1, site, contextFactory)
        # reactor.listenTCP(8080, site)
        change_to_user()
        reactor.run()
    else:

        log.startLogging(sys.stdout)

        factory = WebSocketServerFactory(f"ws://0.0.0.0:{config.port}")
        factory.protocol = WebSocketServer
        # factory.setProtocolOptions(maxConnections=2)

        # note to self: if using putChild, the child must be bytes...
        reactor.listenTCP(config.port, factory)
        change_to_user()
        reactor.run()


if __name__=="__main__":
    main()