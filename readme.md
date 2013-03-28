<a id="top"></a>
**Exposable** is a Python class that can be used to selectively add attribute read/write access to other Python classes. It can be used as a mixin, a context manager, or a wrapper.

## Why'd I Make This?

[[Skip to bottom.]](#why)

## As a Mixin

With the **Exposable** class I can do the following:

    class App(Exposable):

        def __init__(self):

            self._a = 1
            self._b = 2

        @property
        @expose
        def a(self):
            ...
            return self._a

        @property
        def b(self):
            ...
            return self._b

    app = App()
    app.get('a')  # 1
    app.get('b')  # None

That is, I add the *@expose* decorator to the property function and make calls for attribute access through the mixed in *get* method. The *a* attribute is read-only. The *b* attribute is inaccessible. If I want to make the *a* attribute writeable I can apply the *@expose* decorator to its property setter:

    class App(Exposable):

        ...

        @a.setter
        @expose
        def a(self, value):
            self._a = value

    app = App()
    app.set('a')  # True; successfully set a
    app.set('b')  # False; did not successfully set b

The *set* mixin method will return True if the attribute change was successful, and False otherwise.

## As a Context Manager

Sometimes you don't want to mess with your classes. You don't want to 'mix in' anything. So the **Exposable** class can also be used as a context manager. You pass in the instance you want to expose, and a policy for this particular exposing:

    class App(object):

        ...  # same as above

    app = App()

    policy = dict(
        exposed={'a'}
        gettable={'b'}
        settable={'c'}
    )

    with Exposable(app, policy) as exposee:
        exposee.get('a')  # 1
        exposee.get('b')  # 1
        exposee.get('c')  # None

The policy is a simple dictionary of sets. The 'exposed' set exposes attributes with both read and write access. The 'gettable' set exposes attributes with read access. The 'settable' set exposes attributes with write access.

A policy may be defined elsewhere (on some user object, or what-have-you). You can apply them to apps on a case-by-case basis with **Exposable** context manager.

## As a Wrapper

If you look at how the **Exposable** class is being used as a context manager, you'll see that it's just a wrapper beneath the hood. This means that you can use it as such:

    app = App()
    policy = dict(
        exposed={'a'}
        gettable={'b'}
        settable={'c'}
    )
    exposee = Exposable(app, policy)
    exposee.get('a')  # 1

### A Note on Properties

When the **Exposable** class is used as a mixin, your attributes are required to be implemented as properties. That is, a call such as

    app.get('a')

will only work on a mixin instance if *a* is a property. If it's not, then None will be returned.

When the **Exposable** class is used to manage context, or as a wrapper, then the attributes you are exposing/unexposing *are not required* to be properties (but very well may be).

## There's More! (tm)

I get carried away sometimes.

### Mutliple Attribute Access

You can get and set mutliple attributes simultaneously by sending iterables (like a list) to the *get* mixin method, and mappables (like a dict) to the *set* mixin method. Here's a class:

    class App(Exposable):

        def __init__(self):

            self._a = 1
            self._b = 2
            self._c = 3

        @property
        @expose
        def a(self):
            ...
            return self._a

        @a.setter
        @expose
        def a(self, value):
            self._a = value

        @property
        @expose
        def b(self):
            ...
            return self._b

        @property
        def c(self):
            ...
            return self._c

Getting with an iterable (aka list, aka array for javascripty's):

    app.get(['a', 'b', 'c'])

will return:

    {
        'a': 1,
        'b': 2,
        'c': None
    }

Setting with a dictionary (aka hashmap, aka object literal for javascripty's):

    app.set({
        'a': 10,
        'b': 20,
        'c': 30
    })

will return a mapping of True/False values to indicate whether or not the setting(s) were successful:

    {
        'a': True,
        'b': False,
        'c': False
    }

The *get* method:

    pass in             get back
    -------             --------
    a single value      a single value
    an iterable         a dictionary of key-values

The *set* method:

    pass in             get back
    -------             --------
    a single value      a single value
    a dictionary        a dictionary of key-values

### Regexes

If you're using the **Exposable** class as a context manager or wrapper, you can use regexes to specify the policy:

    policy = dict(
        exposed={'b+'}
    )

With this policy, all attributes containing a 'b' are fully exposed:

     class App(object):

        def __init__(self):

            self.a = 1
            self.b = 2
            self.b2 = 2.5
            self.c = 3

    app = App()

    with Exposable(app, policy) as e:
        e.get('a')   # None
        e.get('b')   # 2
        e.get('b2')  # 2.5
        e.get('c')   # None
        e.set('a')   # False
        e.set('b')   # True
        e.set('b2')  # True
        e.set('c')   # False

### Callables

Sometimes regexes are just a pain. If you're using the **Exposable** class as a context manager or wrapper, you can also use predicates (callables (like a function) that return a boolean). The callables must accept a single parameter - the attribute name you are trying to access - and then return a Truthy or Falsey value to indicate whether the attribute is accessible:

    def is_ok(s):

        if s.startswith('a'):
            return True

    policy = dict(
        exposed={is_ok, lambda s: s.startswith('b')}
    )

    exposee = Exposable(foo, policy)

<a id="why"></a>
## Why'd I Make This?
[[top]](#top)

I'm writing/have written (what amounts to) an "application server" in Python & Javascript. User apps have two interrelated parts: a front-end js part, and potentially a back-end python part (if server-side logic is required). Sometimes I'd like the js part of the app to read/write attributes of the python part. It is tedious to have to check selectively against attribute access:

    // js

    promise = me.getAttr(["a", "b"]); // 'me' is a js app of some kind
    promise.done(function (response) {
        console.log(response.a);  // prints '1'
        console.log(response.b);  // prints 'null'; JSON converts my Python None value into a null
    });

    # python

    class SomePythonAppThatCounterpartsTheJsAppAbove(object):

        def __init__(self):

            self._a = 1
            self._b = 2

        @property
        def a(self):
            ...
            return self._a

        @property
        def b(self):
            ...
            return self._b

        def on_get(self, attr):

            allowed = ['a']
            if attr in allowed:
                try:
                    return getattr(self, attr)
                except AttributeError:
                    pass

            # an implicit None value is returned here

This works fine and all, but the definition of the SomePythonAppThatCounterpartsTheJsAppAbove (from hereon called App) class is fluid, and as I add/remove/alter attributes I also need to remember to update that 'allowed' list inside the on_get method.

With the **Exposable** class I can simply decorate or undecorate the attributes as I add them, remove them, rename them, or alter what they mean.

However, I also realized that sometimes the permissions on server-side app attributes were user-dependant. An admin required access to some parts of an app that a regular user would never have access to. Ideally I wanted to grab a "policy" from a user regarding an app in question, and then apply that policy to the app whenever the user requested access to attributes. So the **Exposable** class mutated into a wrapper, and then (because it was so simple!) a context manager.

[[top]](#top)

## Install'n It

Sorry, this isn't on [PyPi](https://pypi.python.org/pypi). But you can download the files from here, on GitHub, and import at your leisure.

## Use'n It

    from exposable import Exposable, expose

Then mixin & decorate or manage contextually/wrap. Also, see tests.

## Date'n It

This was assembled for publication on the 28th of March, 2013. The versions of the software used at that time were:

1. [Python 2.7.x](http://www.python.org/download/releases/2.7.3/)
2. [Python 3.2.x](http://www.python.org/download/releases/3.2.3/)
