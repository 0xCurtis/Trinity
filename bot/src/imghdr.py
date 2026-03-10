import os

try:
    import imghdr
except ImportError:

    class Imghdr:
        _tests = []

        @classmethod
        def what(cls, f, h=None):
            if h is None:
                if isinstance(f, (str, os.PathLike)):
                    with open(f, "rb") as fp:
                        h = fp.read(32)
                else:
                    h = f.read(32)
                    f.seek(-32, 1)

            for test in cls._tests:
                res = test(h, f)
                if res:
                    return res
            return None

        @classmethod
        def test(cls, h, f):
            for test in cls._tests:
                res = test(h, f)
                if res:
                    return res
            return None

    imghdr = Imghdr()

    def test_jpeg(h, f):
        if h[:6] in (
            b"\xff\xd8\xff\xe0\x00\x10",
            b"\xff\xd8\xff\xe1\x00\x10",
            b"\xff\xd8\xff\xdb\x00\x10",
        ):
            return "jpeg"

    imghdr._tests.append(test_jpeg)
