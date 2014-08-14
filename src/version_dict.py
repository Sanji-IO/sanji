import collections
import copy
class VersionDict(collections.MutableMapping):
    """A dictionary that applies an arbitrary key-altering
       function before accessing the keys"""

    def __init__(self, *args, **kwargs):
        self.store = dict()
        self.update(dict(*args, **kwargs))  # use the free update to set keys
        self.private_head = "private"
        self.public_head = "public"
        self.store[self.private_head] = dict()
        self.store[self.public_head] = dict()
        self.store[self.private_head]["version"] = 0

    def __getitem__(self, key):
        return self.store[self.public_head][key]

    def __setitem__(self, key, value):
        self.store[self.public_head][key] = value

    def __delitem__(self, key):
        del self.store[self.public_head][key]

    def __iter__(self):
        return iter(self.store[self.public_head])

    def __len__(self):
        return len(self.store[self.public_head])

    def __str__(self):
        return str(self.store[self.public_head])

    def __repr__(self):
        return self.store[self.public_head]

    def get_private(self):
        return self.store[self.private_head]

    def deepcopy(self, dictionary):
        self.store = copy.deepcopy(dictionary)


class SanjiJSON(VersionDict):
    def __init__(self, file_path):
        
        pass




if __name__ == "__main__":
    s = VersionDict()
    s['Test'] = 5
    s['Bat'] = "Yang"

    print s

    A = dict()
    A['private'] = dict()
    A['private']['version'] = 300
    A['private']['obj'] = dict()
    A['private']['obj']['name'] = "John"
    A['public'] = dict()
    A['public']['ip'] = "192.168.31.254"

    cc = VersionDict()
    cc.deepcopy(A)
    private = cc.get_private()
    print private
    private["obj"]["name"] = "Matt"
    print cc