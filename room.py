class Room():
    rooms = dict()
    def __init__(self, name):
        self.name = name
        self.users = []

    def get(self):
        print(self.name, self.rooms.keys())
        if self.name in self.rooms:
            return self.rooms[self.name]

    def set(self):
        if self.name not in self.rooms:
            self.rooms[self.name] = self

    def add(self, user):
        for u in self.users:
            if u.name == user.name:
                return [False, "Already logged in"]
        self.users.append(user)
        return [True, "Joined"]

    def remove(self, object=None, type="user"):
        users = self.users
        rooms = self.rooms
        if type == "user":
            for user in users:
                if object:
                    if user.uid == object:
                        user.setRoom(None)
                        self.users.remove(user)
        if type == "room":
            if object in rooms:
                del self.rooms[object]
            if not object:
                del self.rooms[self.name]

    def write(self, **commands):
        for user in self.users:
            user.write(**commands)

