

from exposable import Exposable, exposed


class Foo(Exposable):

    def __init__(self):

        self._a = 1
        self._b = 2
        self._c = 3
        self.d = 4  # an unexposed non-property attribute

    # a completely exposed property 'a'
    @property
    @exposed
    def a(self):
        return self._a

    @a.setter
    @exposed
    def a(self, value):
        self._a = value

    # a read-only exposed property 'b'
    @property
    @exposed
    def b(self):
        return self._b

    @b.setter
    def b(self, value):
        self._b = value

    # an unexposed property 'c'
    @property
    def c(self):
        return self._c

    # an unexposed, non-property function 'e'
    def e(self):
        return 5


def assert_exception(fn, exception_type):

    exception = None
    try:
        fn()
    except Exception as ex:
        exception = ex

    return isinstance(exception, exception_type)


def test_mixin():

    print ("\n######## text_mixin() ########")

    foo = Foo()

    def base_test(foo):

        print ("\n---Normal calls---")
        assert foo.a == 1
        assert foo.b == 2
        assert foo.c == 3
        assert foo.d == 4
        assert foo.e() == 5

        print ("\n---Exposable API calls---")
        assert foo.get('a') == 1
        assert foo.get('b') == 2
        assert foo.get('c') is None
        assert foo.get('d') is None
        assert foo.get('e') is None

        foo.set('a', 10)
        foo.set('b', 20)
        foo.set('c', 30)
        foo.set('d', 40)
        foo.set('e', 50)

        assert foo.get('a') == 10
        assert foo.get('b') == 2
        assert foo.get('c') is None
        assert foo.get('d') is None
        assert foo.get('e') is None

    base_test(foo)

    print ("\n[Unexposing 'a']")
    foo.unexpose('a')
    assert foo.get('a') is None
    assert foo.a == 10

    print ("\n[Re-exposing 'a']")
    foo.expose('a')
    assert foo.get('a') == foo.a == 10

    print ("\n[Writing to 'a']")
    foo.set('a', 1)
    assert foo.get('a') == foo.a == 1

    print ("\n[Unexposing write access on 'a']")
    foo.unexpose('a', 'setter')
    foo.set('a', 10)  # try to set it
    assert foo.get('a') == foo.a == 1

    print ("\n[Unexposing read access on 'a']")
    foo.unexpose('a', 'getter')
    assert foo.get('a') is None
    assert foo.a == 1

    print ("\n[Exposing read access on 'a']")
    foo.expose('a', 'getter')
    foo.set('a', 100)  # try to set it
    assert foo.get('a') == foo.a == 1

    print ("\n[Exposing write access on 'a']")
    foo.expose('a', 'setter')
    foo.set('a', 100)
    assert foo.get('a') == foo.a == 100

    foo.set('a', 1)
    base_test(foo)

    assert foo.get(['a', 'b', 'c']) == {"a": 10, "b": 2, "c": None}


def test_context():

    print ("\n######## text_context() ########")

    foo = Foo()
    foo.b2 = 0

    policy = dict(
        exposed={'a'},    # attr 'a' is gettable and settable
        gettable={'c'},   # attr 'c' is gettable, but not settable
        settable={'b+'}   # any attr containing a 'b' is settable
    )

    print ("\n---Exposable API calls via context management (with)---")

    with Exposable(foo, policy) as exposee:

        assert exposee.get('a') == 1
        assert exposee.get('b') is None
        assert exposee.get('c') == 3
        assert exposee.get('d') is None
        assert exposee.get('e') is None
        assert exposee.get(['a', 'b', 'c']) == {'a': 1, 'b': None, 'c': 3}

        exposee.set('a', 10)
        exposee.set('b', 20)
        exposee.set('c', 30)
        exposee.set('d', 40)
        exposee.set('e', 50)

        assert exposee.get('a') == 10
        assert exposee.get('b') is None
        assert foo.b == 20
        assert exposee.get('c') == 3
        assert exposee.get('d') is None
        assert exposee.get('e') is None

        exposee.set(dict(
            a=100,
            b=200,
            b2=-1,
            c=300,
            d=400,
            e=500
        ))

        assert exposee.get('a') == 100
        assert exposee.get('b') is None
        assert foo.b == 200
        assert exposee.get('b2') is None
        assert foo.b2 == -1
        assert exposee.get('c') == 3
        assert exposee.get('d') is None
        assert exposee.get('e') is None

    foo = Foo()

    policy = dict(
        exposed={'[a-zA-Z]+'}  # all attrs but '_' are read/write-able!
    )

    print ("\n---Regexing Exposable API calls "
           "via context management (with)---")

    with Exposable(foo, policy) as exposee:

        assert exposee.get('a') == 1
        assert exposee.get('b') == 2
        assert exposee.get('c') == 3
        assert exposee.get('d') == 4
        assert exposee.get('e') == foo.e
        assert exposee.get(['a', 'b', 'c']) == {'a': 1, 'b': 2, 'c': 3}

        exposee.set('a', 10)
        exposee.set('b', 20)
        exposee.set('c', 30)
        exposee.set('d', 40)
        exposee.set('e', 50)

        assert exposee.get('a') == 10
        assert exposee.get('b') == 20
        assert exposee.get('c') == 3
        assert exposee.get('d') == 40
        assert exposee.get('e') == 50
        assert (
            exposee.get(['a', 'b', 'c', 'd', 'e']) ==
            {
                'a': 10,
                'b': 20,
                'c': 3,
                'd': 40,
                'e': 50
            }
        )

        exposee.set(dict(
            a=100,
            b=200,
            c=300,
            d=400,
            e=500
        ))

        assert exposee.get('a') == 100
        assert exposee.get('b') == 200
        assert exposee.get('c') == 3
        assert exposee.get('d') == 400
        assert exposee.get('e') == 500
        assert (
            exposee.get(['a', 'b', 'c', 'd', 'e']) ==
            {
                'a': 100,
                'b': 200,
                'c': 3,
                'd': 400,
                'e': 500
            }
        )

        assert_exception(lambda: exposee.set(['a']), TypeError)


def test_wrapper():

    print ("\n######## text_wrapper() ########")

    foo = Foo()
    policy = dict(
        exposed={'a'},
        gettable={'c'},
        settable={'b+'}
    )
    exposee = Exposable(foo, policy)
    print ("\n---Exposable API calls via wrapping, with predicates---")

    assert exposee.get('a') == 1
    assert exposee.get('b') is None
    assert exposee.get('c') == 3
    assert exposee.get('d') is None
    assert exposee.get('e') is None
    assert exposee.get(['a', 'b', 'c']) == {'a': 1, 'b': None, 'c': 3}

    exposee.set('a', 10)
    exposee.set('b', 20)
    exposee.set('c', 30)
    exposee.set('d', 40)
    exposee.set('e', 50)

    assert exposee.get('a') == 10
    assert exposee.get('b') is None
    assert foo.b == 20
    assert exposee.get('c') == 3
    assert exposee.get('d') is None
    assert exposee.get('e') is None

    exposee.set(dict(
        a=100,
        b=200,
        b2=-1,
        c=300,
        d=400,
        e=500
    ))

    assert exposee.get('a') == 100
    assert exposee.get('b') is None
    assert foo.b == 200
    assert exposee.get('b2') is None
    assert foo.b2 == -1
    assert exposee.get('c') == 3
    assert exposee.get('d') is None
    assert exposee.get('e') is None

    assert exposee.get([1, 2]) == {1: None, 2: None}

    def is_ok(s):

        if s.startswith('a'):
            return True

    policy = dict(
        exposed={is_ok, lambda s: s.startswith('b')}
    )

    exposee = Exposable(foo, policy)

    exposee.set('a', 1000)
    exposee.set('b', 2000)
    exposee.set('c', 3000)
    exposee.set('d', 4000)
    exposee.set('e', 5000)

    import types

    assert foo.a == 1000
    assert foo.b == 2000
    assert foo.c == 3
    assert foo.d == 4
    assert isinstance(foo.e, types.MethodType)


if __name__ == '__main__':

    """
    Tested on Python 2.7.3+ (including Python 3.x)
    """

    test_mixin()
    test_context()
    test_wrapper()
    print ("\nALL IS WELL.")
