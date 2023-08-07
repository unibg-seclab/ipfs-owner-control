class Node:
    def __init__(self, value, children=None):
        self.value = value
        self.children = children if children is not None else {}

    def contents(self):
        return self.children.keys()

    def add_child(self, key, child):
        self.children[key] = child

    def to_dict(self):
        to_write_children = {}
        for k, node in self.children.items():
            to_write_children[k] = node.to_dict()

        value = self.value.to_dict() if hasattr(self.value, 'to_dict') else self.value
        return {
            'value': value,
            'children': to_write_children
        }

    @staticmethod
    def from_dict(data, transform=None):
        value = transform(data['value']) if transform is not None else data['value']
        children = {}
        for k, child in data['children'].items():
            children[k] = Node.from_dict(child, transform)

        return Node(value, children)


class Trie:
    def __init__(self, root=None):
        if isinstance(root, Node):
            self.root = root
        else:
            self.root = Node(root)

    # ------------------------------------------------------ Dict conversions

    def to_dict(self):
        return self.root.to_dict()

    @staticmethod
    def from_dict(data, transform=None):
        return Trie(Node.from_dict(data, transform))

    # ------------------------------------------------------ Inserting and moving around

    def insert(self, keys, new_node):
        last = len(keys) - 1

        node = self.root
        for i, key in enumerate(keys):
            if i == last:
                node.children[key] = new_node
            elif key in node.children:
                node = node.children[key]
            else:
                tmp = Node(None)
                node.children[key] = tmp
                node = tmp

    def move(self, from_keys, to_keys):
        node = self[from_keys]
        if node is not None:
            del self[to_keys]
            self.insert(to_keys, node)
            del self[from_keys]

    # ------------------------------------------------------ Dunder methods

    def __contains__(self, keys):
        return self[keys] is not None

    def __getitem__(self, keys):
        node = self.root
        for k in keys:
            if k in node.children:
                node = node.children[k]
            else:
                return None

        return node

    def __setitem__(self, keys, new_node):
        self.insert(keys, new_node)

    def __delitem__(self, keys):
        node = self.root
        last = len(keys) - 1

        for i, key in enumerate(keys):
            if key not in node.children:
                return

            if i == last:
                del node.children[key]
            else:
                node = node.children[key]
