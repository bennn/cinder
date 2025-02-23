import unittest

from .common import StaticTestBase


class NonStaticInheritanceTests(StaticTestBase):
    def test_static_return_is_resolved_with_multiple_levels_of_inheritance(self):
        codestr = """
            class C:
                def foobar(self, x: int) -> int:
                    return x
                def f(self) -> int:
                    return self.foobar(1)
        """
        with self.in_strict_module(codestr, name="mymod", enable_patching=True) as mod:
            C = mod.C

            class D(C):
                def foobar(self, x: int) -> int:
                    return x + 1

            class E(D):
                def foobar(self, x: int) -> int:
                    return x + 2

            self.assertEqual(D().f(), 2)
            self.assertEqual(E().f(), 3)

    def test_multiple_inheritance_initialization(self):
        """Primarily testing that when we have multiple inheritance that
        we safely initialize all of our v-tables.  Previously we could
        init B2 while initializing the bases for DM, and then we wouldn't
        initialize the classes derived from it."""

        codestr = """
            class C:
                def foobar(self, x: int) -> int:
                    return x
                def f(self) -> int:
                    return self.foobar(1)
                def g(self): pass

            def f(x: C):
                return x.f()
        """
        with self.in_strict_module(codestr, name="mymod", enable_patching=True) as mod:
            C = mod.C
            f = mod.f

            class B1(C):
                def f(self):
                    return 10

            class B2(C):
                def f(self):
                    return 20

            class D(B2):
                def f(self):
                    return 30

            class DM(B2, B1):
                pass

            # Force initialization of C down
            C.g = 42
            self.assertEqual(f(B1()), 10)
            self.assertEqual(f(B2()), 20)
            self.assertEqual(f(D()), 30)
            self.assertEqual(f(DM()), 20)

    def test_multiple_inheritance_initialization_invoke_only(self):
        """Primarily testing that when we have multiple inheritance that
        we safely initialize all of our v-tables.  Previously we could
        init B2 while initializing the bases for DM, and then we wouldn't
        initialize the classes derived from it."""

        codestr = """
            class C:
                def foobar(self, x: int) -> int:
                    return x
                def f(self) -> int:
                    return self.foobar(1)
                def g(self): pass

            def f(x: C):
                return x.f()
        """
        with self.in_strict_module(codestr, name="mymod", enable_patching=True) as mod:
            C = mod.C
            f = mod.f

            class B1(C):
                def f(self):
                    return 10

            class B2(C):
                def f(self):
                    return 20

            class D(B2):
                def f(self):
                    return 30

            class DM(B2, B1):
                pass

            # No forced initialization, only invokes
            self.assertEqual(f(C()), 1)
            self.assertEqual(f(B1()), 10)
            self.assertEqual(f(B2()), 20)
            self.assertEqual(f(D()), 30)
            self.assertEqual(f(DM()), 20)

    def test_inherit_abc(self):
        codestr = """
            from abc import ABC

            class C(ABC):
                @property
                def f(self) -> int:
                    return 42

                def g(self) -> int:
                    return self.f
        """
        with self.in_module(codestr) as mod:
            C = mod.C
            a = C()
            self.assertEqual(a.g(), 42)

    def test_static_decorator_non_static_class(self):
        codestr = """
            def mydec(f):
                def wrapper(*args, **kwargs):
                    return f(*args, **kwargs)
                return wrapper

            class B:
                def g(self): pass

            def f(x: B):
                return x.g()
        """
        with self.in_module(codestr) as mod:
            mydec = mod.mydec
            B = mod.B
            f = mod.f

            # force v-table initialization on base
            f(B())

            class D(B):
                @mydec
                def f(self):
                    pass

            self.assertEqual(D().f(), None)
            D.f = lambda self: 42
            self.assertEqual(f(B()), None)
            self.assertEqual(f(D()), None)
            self.assertEqual(D().f(), 42)

    def test_nonstatic_multiple_inheritance_invoke(self):
        """multiple inheritance from non-static classes should
        result in only static classes in the v-table"""

        codestr = """
        def f(x: str):
            return x.encode('utf8')
        """

        class C:
            pass

        class D(C, str):
            pass

        with self.in_module(codestr) as mod:
            self.assertEqual(mod.f(D("abc")), b"abc")

    def test_nonstatic_multiple_inheritance_invoke_static_base(self):
        codestr = """
        class B:
            def f(self):
                return 42

        def f(x: B):
            return x.f()
        """

        class C:
            def f(self):
                return "abc"

        with self.in_module(codestr) as mod:

            class D(C, mod.B):
                pass

            self.assertEqual(mod.f(D()), "abc")

    def test_nonstatic_multiple_inheritance_invoke_static_base_2(self):
        codestr = """
        class B:
            def f(self):
                return 42

        def f(x: B):
            return x.f()
        """

        class C:
            def f(self):
                return "abc"

        with self.in_module(codestr) as mod:

            class D(C, mod.B):
                def f(self):
                    return "foo"

            self.assertEqual(mod.f(D()), "foo")

    def test_no_inherit_multiple_static_bases(self):
        codestr = """
            class A:
                pass

            class B:
                pass
        """
        with self.in_module(codestr) as mod:
            with self.assertRaisesRegex(
                TypeError, r"multiple bases have instance lay-out conflict"
            ):

                class C(mod.A, mod.B):
                    pass

    def test_no_inherit_multiple_static_bases_indirect(self):
        codestr = """
            class A:
                pass

            class B:
                pass
        """
        with self.in_module(codestr) as mod:

            class C(mod.B):
                pass

            with self.assertRaisesRegex(
                TypeError, r"multiple bases have instance lay-out conflict"
            ):

                class D(C, mod.A):
                    pass

    def test_no_inherit_static_and_builtin(self):
        codestr = """
            class A:
                pass
        """
        with self.in_module(codestr) as mod:
            with self.assertRaisesRegex(
                TypeError, r"multiple bases have instance lay-out conflict"
            ):

                class C(mod.A, str):
                    pass


if __name__ == "__main__":

    unittest.main()
