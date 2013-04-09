import re
import types
import collections


def exposed(o):

    o.exposed = True
    return o


class Exposable(object):

    """
    See readme.md and test_exposable.py
    """

    def __init__(self, wrapee=None, policy=None):

        self._wrapee = wrapee
        self._policy = policy if policy else {}

        self._policy.setdefault('exposed', set())
        self._policy.setdefault('gettable', set())
        self._policy.setdefault('settable', set())

        self._policy['exposed'] = {
            p for p in [_c(p) for p in self._policy['exposed']]
        }
        self._policy['gettable'] = {
            p for p in [_c(p) for p in self._policy['gettable']]
        }
        self._policy['settable'] = {
            p for p in [_c(p) for p in self._policy['settable']]
        }

    def __enter__(self):

        return self

    def __exit__(self, exc_type, exc_value, traceback):

        pass

    def get(self, attrs):

        if (isinstance(attrs, basestring) or
           not isinstance(attrs, collections.Iterable)):
            attrs = [attrs]

        try:
            w = self._wrapee
        except AttributeError:

            d = {}
            for attr in attrs:
                fn = self._get_property_function(attr, 'getter')
                if fn and fn.__dict__.get('exposed', None):
                    d[attr] = getattr(self, attr)
                else:
                    d[attr] = None

            if len(attrs) == 1:
                return d.values()[0]

            return d or None

        readable = self._policy['gettable']
        exposed = self._policy['exposed']
        d = {}

        for attr in attrs:
            if any([_search(p, attr) for p in readable.union(exposed)]):  # attr in readable.union(exposed):
                d[attr] = getattr(w, attr)
            else:
                d[attr] = None

        if len(attrs) == 1:
            return d.values()[0]

        return d or None

    def set(self, attrs, value=None):

        if isinstance(attrs, basestring):
            attrs = {attrs: value}

        if not isinstance(attrs, collections.Mapping):
            raise TypeError(
                "The attr or attrs passed to set must by a basestring "
                "type or a collections.Mapping."
            )
        try:
            w = self._wrapee
        except AttributeError:

            d = {}

            for attr, value in attrs.items():
                fn = self._get_property_function(attr, 'setter')
                if fn and fn.__dict__.get('exposed', None):
                    setattr(self, attr, value)
                    d[attr] = True
                else:
                    d[attr] = False

            if len(attrs) == 1:
                return d.values()[0]

            return d

        writeable = self._policy['settable']
        exposed = self._policy['exposed']
        d = {}

        for attr, value in attrs.items():
            if any([_search(p, attr) for p in writeable.union(exposed)]):
                try:
                    setattr(w, attr, value)
                    d[attr] = True
                except AttributeError:  # attr as defined is a read-only
                                        # property (it has no setter)
                    d[attr] = False

            else:
                d[attr] = False

        if len(attrs) == 1:
            return d.values()[0]

        return d

    def unexpose(self, attr, kind="both"):

        try:
            o = self._wrapee
        except AttributeError:
            o = self

        if kind in ("both", "getter"):
            fn = o._get_property_function(attr, 'getter')
            if fn:
                fn.exposed = False
        if kind in ("both", "setter"):
            fn = o._get_property_function(attr, 'setter')
            if fn:
                fn.exposed = False

    def expose(self, attr, kind="both"):

        try:
            o = self._wrapee
        except AttributeError:
            o = self

        if kind in ("both", "getter"):
            fn = o._get_property_function(attr, 'getter')
            if fn:
                fn.exposed = True
        if kind in ("both", "setter"):
            fn = o._get_property_function(attr, 'setter')
            if fn:
                fn.exposed = True

    def _get_property_function(self, attr, kind='getter'):

        try:
            o = self._wrapee
        except AttributeError:
            o = self

        try:
            if kind == "getter":
                return o.__class__.__dict__[attr].fget
            elif kind == "setter":
                return o.__class__.__dict__[attr].fset

        except KeyError:  # attr doesn't exist
            pass
        except AttributeError:  # attr is not a property descriptor
            pass


def _search(o, attr):

    if callable(o):
        return o(attr)

    try:
        return o.search(attr)
    except TypeError:
        pass


def _c(a):

    if callable(a):
        return a

    try:
        return re.compile(a)
    except re.error:
        return None
