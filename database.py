import hashlib
import json, config, time, util
from objectify import Objectify

class Database:
    def __init__(self, dbname=config.dbname):
        self.db = Objectify(self.open(dbname))
        self.dbname = dbname
        if config.setup_db:
            self.setup_db()
    
    def addVerifyKey(self, name):
        key = util.generate_id()
        self.db.get("verify").set(name, key)
        return key
    
    def removeVerifyKey(self, name, key):
        if self.db.get("verify").get(name) == key:
            del self.db.get("verify")[name]
            self.save()
    
    def checkVerify(self, name, key):
        if self.db.get("verify").get(name) == key:
            return True
    
    def setVerified(self, name):
        if self.getUser(name):
            self.db.get("users").get(name).set("verified", True)
            self.save()
            return True

    def check(self, name, password):
        user = self.db.users.get(name)
        password = util.generate_uid(config.passwordsalt + password + config.passwordsalt, hash=hashlib.sha3_512)
        if user.password == password and user.name.lower() == name.lower():
            return True
    
    def addUser(self, name, email, password):
        if not self.getUser(name):
            user = {
                "name": name,
                "email": email,
                "password": util.generate_uid(config.passwordsalt + password + config.passwordsalt, hash=hashlib.sha3_512),
                "owns": [],
                "verified": False,
                "time": time.time()

            }
            self.db.get("users").set(name, user)
            self.save()
            return True
        return False
    
    def setForgotPasswordKey(self, name):
        key = util.generate_id()
        self.db.get("forgot").set(key, name)
        self.save()
        return key
    
    def removeKey(self, key):
        del self.db.get("forgot")[key]
        self.save()

    def checkForgotKey(self, name, key):
        if self.db.get("forgot").get(key) == name:
            return True
        return False

    def setPassword(self, name, password, key):
        if self.checkForgotKey(name, key):
            if self.getUser(name):
                self.db.users.get(name)[password] = util.generate_uid(config.passwordsalt + password + config.passwordsalt, hash=hashlib.sha3_512)
                self.save()
                return True
            else:
                return False
        else:
            return False

    def getUser(self, name):
        user = self.db.get("users").get(name)
        if user.isEmpty():
            return False
        return user
    

    
    def save(self):
        js = json.dumps(self.db.toDict()).encode()
        encrypted = util.FCipher(config.path_to_key).encrypt(js)
        f = open(self.dbname, "wb")
        f.write(encrypted)
        f.close()
    
    def open(self, db):
        try:
            f = open(db, "rb")
            encrypted = f.read()
            f.close()
            return json.loads(util.FCipher(config.path_to_key).decrypt(encrypted))
        except:
            return {}
    
    def setup_db(self):
        self.db.set("rooms", {})
        self.db.set("users", {})
        self.db.set("messages", {})
        self.db.set("bans", {})
        self.db.set("forgot", {})
        self.db.set("verify", {})
        self.save()
    
    def addRoom(self, room, owner, title="Example", description="Example Group"):
        name = self.db.get("rooms").get(room)
        if not name.isEmpty():
            return False
        else:
            ro = {
                "name": room,
                "owner": owner,
                "title": util.filter(title),
                "description": util.filter(description),
                "created": time.time(),
                "mods": {}
            }
            self.db.get("users").get(owner).owns.append(room)
            self.db.rooms.set(room, ro)
            self.db.get("messages").set(room, {"messages": []})
            self.db.get("bans").set(room, {"bans": []})
            self.db.get("mods").set(room, {"mods": []})
            self.save()
            return True
    
    def addMessage(self, room, user, ip, uid, body, mid):
        if self.getRoom(room):
            m = self.db.get("messages").get(room)
            if not m.isEmpty():
                message = {
                    "name": room,
                    "user": user,
                    "uid": uid,
                    "ip": ip,
                    "body": body,
                    "mid": mid,
                    "time": time.time()
                }
                m.get("messages").append(message)
            self.save()


    def removeMessagesByUser(self, room, user):
        copy = []
        count = 0
        if self.getRoom(room):
            messages = self.db.get("messages").get(room).get("messages")
            copy += messages
            for message in copy:
                message = Objectify(message)
                if message.user == user:
                    messages.remove(message)
                count += 1
        self.save()
        return count
    
    
    def removeMessageById(self, room, mid):
        if self.getRoom(room):
            messages = self.db.get("messages").get(room).get("messages")
            if Objectify.isList(messages):
                new_list = messages
                for message in new_list:
                    obj_message = Objectify(message)
                    if obj_message.get("mid") == mid:
                        messages.remove(message)
                        return [True, "no-errors"]
                        self.save()
                return [True, "no-errors"]
        else:
            return [False, f"{room} doesn't exist"]

    def setRoomTitle(self, room, title):
        if self.getRoom(room):
            self.db.get("rooms").get(room).title = title
        self.save()
    
    def setRoomDescription(self, room, description):
        if self.getRoom(room):
            self.db.get("rooms").get(room).description = description
        self.save()

    def removeRoom(self, room, owner):
        if self.getRoom(room):
            c = self.db.rooms.get(room).get(owner)
            if not hasattr(c, "isEmpty"):
                del self.db.rooms[room]
                del self.db.mods[room]
                del self.db.bans[room]
                del self.db.messages[room]
                self.db.users.get("owner").owns.remove(room)
                self.save()
    
    def getRoom(self, name):
        room = self.db.get("rooms").get(name)
        if not room.isEmpty():
            return room
    
    def clearRoomMessages(self, room):
        if self.getRoom(room):
            self.db.get("messages").get(room).messages = []
            self.save()
    
    def clearAllMessages(self):
        for room in self.getAllRooms():
            self.clearRoomMessages(room)
    

    def getRoomMessages(self, room):
        if self.getRoom(room):
            if self.db.get("messages").get(room).isEmpty():
                self.db.get("messages").get(room).set("messages", [])
                self.save()
                return self.db.get("messages").get(room).get("messages")
            else:
                return self.db.get("messages").get(room).get("messages")
        else: return []
        
    
    def getMessagesByUser(self, room, user):
        messages = self.getRoomMessages(room)
        user_messages = []
        for message in messages:
            message = Objectify(message)
            if message.get("user") == user:
                user_messages.append(message.toDict())
        return user_messages
    
    def getMessagesByIp(self, room, ip):
        messages = self.getRoomMessages(room)
        ip_message = []
        for message in messages:
            message = Objectify(message)
            if message.get("ip") == ip:
                ip_message.append(message.toDict())
        return ip_message

    def getMessageByUid(self, room, uid):

        messages = self.getRoomMessages(room)
        uid_messages = []
        for message in messages:
            message = Objectify(message)
            if message.get("uid") == uid:
                uid_messages.append(message.toDict())
        return uid_messages

    def getAllRooms(self):

        return list(self.db.get("messages").toDict().keys())
    
    def getAllMessagesByUser(self, user):

        user_messages = {}
        for room in self.getAllRooms():
            messages = self.getMessagesByUser(room, user)
            user_messages[room] = messages
        return user_messages
    
    def getAllMessagesByIp(self, ip):
        ip_messages = {}
        for room in self.getAllRooms():
            messages = self.getMessagesByIp(room, ip)
            ip_messages[room] = messages
        return ip_messages
    
    def getAllMessagesByUid(self, uid):
        uid_messages = {}
        for room in self.getAllRooms():
            messages = self.getAllMessagesByUid(room, uid)
            uid_messages[room] = messages
        return uid_messages

    def addMod(self, room, owner, mod):
        if self.getRoom(room):
            if self.getRoom(room).get("owner").lower() == owner.lower():
                self.db.get("mods").get(room).set(mod.lower(), {
                    "name": mod.lower(),
                    "room": room,
                    "time": time.time()
                })
                self.save()
                return [True, "modded"]
            else:
                return [False, "Not owner"]
    def removeMod(self, room, owner, mod):
        if self.getRoom(room):
            if self.getRoom(room).get("owner").lower() == owner.lower():
                del self.db.get("mods")[mod.lower()]
                self.save()
    
    def getMods(self, room):
        if self.getRoom(room):
            mods = list(self.db.get("mods").toDict().keys())
            mods.append({"owner": self.getRoom(room).owner})
            return mods
        else: 
            return []
    
    def getBannedByUid(self, room, uid):
        bans = self.db.get("bans").get(room)
        for ban in bans:
            ban = Objectify(ban)
            if uid in ban.uids:
                return ban

    def getBannedByName(self, room, name):
        bans = self.db.get("bans").get(room)
        for ban in bans:
            ban = Objectify(ban)
            if name.lower() in ban.names:
                return ban
    
    def addBan(self, room, name, uid, target):
        ban = self.getBannedByUid(room, uid) or self.getBannedByName(room, target)
        if ban:
            if uid not in Objectify(ban).uids:
                ban['uids'].append(uid)
            if target not in ban['names']:
                ban['names'].append(target)
        else:
            ban = {
                "by": name.lower(),
                "names": [target.lower()],
                "room": room,
                "uids": [uid],
                "time": time.time()
            }
            self.db.get("bans").get(room).append(ban)
        self.save()
    
    def removeBan(self, room, target, uid):
        b = []
        bans =  self.db.get("bans").get(room)
        b += bans
        for ban in b:
            ban = Objectify(ban)
            if uid in ban.uids:
                try:
                    bans.remove(ban.toDict())
                except:
                    pass
            if target.lower() in ban.names:
                try:
                    bans.remove(ban.toDict())
                except:
                    pass
        self.save()


    def isBanned(self, room, target, uid):
        ban = self.getBannedByIp(room, ip) or self.getBannedByName(room, target) or self.getBannedByUid(room, uid)
        if ban: return True
        else: return False

