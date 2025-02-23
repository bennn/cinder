import ast
import dis
import inspect
import io
from compiler.pycodegen import PythonCodeGenerator
from .dis_stable import Disassembler
from textwrap import dedent

from .common import CompilerTest


def dump_code(code):
    f = io.StringIO()
    Disassembler().dump_code(code, file=f)
    text = f.getvalue()
    return text


class Python38Tests(CompilerTest):
    maxDiff = None

    def _check(self, src):
        src = dedent(src).strip()
        actual = dump_code(self.compile(src, PythonCodeGenerator))
        expected = dump_code(compile(src, "", mode="exec"))
        self.assertEqual(actual, expected)

    def test_sanity(self) -> None:
        """basic test that the compiler can generate a function"""
        code = self.compile("f()", PythonCodeGenerator)
        self.assertInBytecode(code, "CALL_FUNCTION")
        self.assertEqual(code.co_posonlyargcount, 0)

    def test_walrus_if(self):
        code = self.compile("if x:= y: pass", PythonCodeGenerator)
        self.assertInBytecode(code, "STORE_NAME", "x")

    def test_walrus_call(self):
        code = self.compile("f(x:= y)", PythonCodeGenerator)
        self.assertInBytecode(code, "STORE_NAME", "x")

    def test_while_codegen(self) -> None:
        source = """
            def f(l):
                while x:
                    if y: pass
        """
        self._check(source)

    def test_for_codegen(self) -> None:
        source = """
            def f(l):
                for i, j in l: pass
        """
        self._check(source)

    def test_async_for_codegen(self) -> None:
        source = """
            async def f(l):
                async for i, j in l: pass
        """
        self._check(source)

    def test_continue(self) -> None:
        source = """
            while x:
                if y: continue
                print(1)
        """
        self._check(source)

        source = """
            for y in l:
                if y: continue
                print(1)
        """
        self._check(source)

    def test_break(self) -> None:
        source = """
            while x:
                if y: break
                print(1)
        """
        self._check(source)

        source = """
            for y in l:
                if y: break
                print(1)
        """
        self._check(source)

    def test_try_finally(self):
        source = """
            def g():
                for i in l:
                    try:
                        if i > 0:
                            continue
                        if i == 3:
                            break
                        if i == 5:
                            return
                    except:
                        pass
                    finally: pass
            """
        self._check(source)

        source = """
            def g():
                for i in l:
                    try:
                        if i == 5:
                            return
                    except BaseException as e:
                        print(1)
                    except:
                        pass
                    finally:
                        continue
            """
        self._check(source)

    def test_async_comprehension(self) -> None:
        source = """
            async def f():
                async for z in (x async for x in y if x > 10):
                    yield z
        """
        self._check(source)

        source = """
            async def f():
                return [x async for x in y if x > 10]
        """
        self._check(source)

        source = """
            async def f():
                return {x async for x in y if x > 10}
        """
        self._check(source)

        source = """
            async def f():
                return {x:str(x) async for x in y if x > 10}
        """
        self._check(source)

    def test_try_except(self):
        source = """
            try:
                f()
            except:
                g()
        """
        self._check(source)
        source = """
            try:
                f()
            except BaseException:
                g(e)
        """
        self._check(source)

        source = """
            try:
                f()
            except BaseException as e:
                g(e)
        """
        self._check(source)

    def test_with(self):
        source = """
            with foo():
                pass
        """
        self._check(source)

        source = """
            with foo() as f:
                pass
        """
        self._check(source)

        source = """
            with foo() as f, bar() as b, baz():
                pass
        """
        self._check(source)

    def test_async_with(self):
        source = """
            async def f():
                async with foo():
                    pass
        """
        self._check(source)

        source = """
            async def g():
                async with foo() as f:
                    pass
        """
        self._check(source)

        source = """
            async def g():
                async with foo() as f, bar() as b, baz():
                    pass
        """
        self._check(source)

    def test_constants(self):
        source = """
            # formerly ast.Num
            i = 1
            f = 1.1
            c = 1j
            # formerly ast.Str
            s = "foo"
            b = b"foo"
            # formerly ast.Ellipsis
            e = ...
            # formerly ast.NameConstant
            t = True
            f = False
            n = None
        """
        self._check(source)

    def test_key_value_order(self):
        source = """
order = []
def f(place, val):
    order.append((place, val))

{f('key', k): f('val', v) for k, v in zip('abc', [1, 2, 3])}
        """
        self._check(source)

    def test_return(self):
        source = """
def f():
    return 1
        """
        self._check(source)

        source = """
def f():
    return
        """
        self._check(source)

        source = """
def f():
    return x
        """
        self._check(source)

        source = """
def f():
    try:
        return 1
    finally:
        print(1)
        """
        self._check(source)

    def test_break_continue_in_finally(self):
        source = """
            def test_break_in_finally_after_return(self):
                # See issue #37830
                def g1(x):
                    for count in [0, 1]:
                        count2 = 0
                        while count2 < 20:
                            count2 += 10
                            try:
                                return count + count2
                            finally:
                                if x:
                                    break
                    return 'end', count, count2
                self.assertEqual(g1(False), 10)
                self.assertEqual(g1(True), ('end', 1, 10))

                def g2(x):
                    for count in [0, 1]:
                        for count2 in [10, 20]:
                            try:
                                return count + count2
                            finally:
                                if x:
                                    break
                    return 'end', count, count2

            def test_continue_in_finally_after_return(self):
                # See issue #37830
                def g1(x):
                    count = 0
                    while count < 100:
                        count += 1
                        try:
                            return count
                        finally:
                            if x:
                                continue
                    return 'end', count

                def g2(x):
                    for count in [0, 1]:
                        try:
                            return count
                        finally:
                            if x:
                                continue
                    return 'end', count
        """
        self._check(source)

    def test_continue_in_finally(self):
        source = """
            def test_continue_in_finally(self):
                count = 0
                while count < 2:
                    count += 1
                    try:
                        pass
                    finally:
                        continue
                    break

                count = 0
                while count < 2:
                    count += 1
                    try:
                        break
                    finally:
                        continue

                count = 0
                while count < 2:
                    count += 1
                    try:
                        1/0
                    finally:
                        continue
                    break

                for count in [0, 1]:
                    try:
                        pass
                    finally:
                        continue
                    break

                for count in [0, 1]:
                    try:
                        break
                    finally:
                        continue

                for count in [0, 1]:
                    try:
                        1/0
                    finally:
                        continue
                    break
        """
        self._check(source)

    def test_asyncgen(self):
        source = """
            async def f(it):
                for i in it:
                    yield i

            async def run_list():
                return [i + 10 async for i in f(range(5)) if 0 < i < 4]

            async def run_set():
                return {i + 10 async for i in f(range(5)) if 0 < i < 4}

            async def run_dict():
                return {i + 10: i + 100 async for i in f(range(5)) if 0 < i < 4}

            async def run_gen():
                gen = (i + 10 async for i in f(range(5)) if 0 < i < 4)
                return [g + 100 async for g in gen]
        """
        self._check(source)

    def test_posonly_args(self):
        code = self.compile("def f(a, /, b): pass", PythonCodeGenerator)

        f = self.find_code(code)
        self.assertEqual(f.co_posonlyargcount, 1)
        self.assertEqual(f.co_argcount, 2)
        self.assertEqual(f.co_varnames, ("a", "b"))

    def test_multiline_expr_line_nos(self):
        codestr = """
            import traceback

            def some_inner(k, v):
                a = 1
                b = 2
                return traceback.StackSummary.extract(
                    traceback.walk_stack(None), capture_locals=True, limit=1)
        """
        self._check(codestr)

    def test_decorator_line_nos(self):
        dec_func = """
            @a
            @b
            @c
            def x():
                pass
        """
        self._check(dec_func)

        dec_class = """
            @a
            @b
            @c
            class C():
                pass
        """
        self._check(dec_class)

        dec_async_func = """
            @a
            @b
            @c
            async def x():
                pass
        """
        self._check(dec_async_func)

    def test_yield_outside_function_dead_code(self):
        """Yield syntax errors are still reported in dead code: bpo-37500."""
        cases = [
            "if 0: yield",
            "class C:\n    if 0: yield",
            "if 0: yield\nelse:  x=1",
            "if 1: pass\nelse: yield",
            "while 0: yield",
            "while 0: yield\nelse:  x=1",
            "class C:\n  if 0: yield",
            "class C:\n  if 1: pass\n  else: yield",
            "class C:\n  while 0: yield",
            "class C:\n  while 0: yield\n  else:  x = 1",
        ]
        for case in cases:
            with self.subTest(case):
                with self.assertRaisesRegex(SyntaxError, "outside function"):
                    self.compile(case)

    def test_return_outside_function_dead_code(self):
        """Return syntax errors are still reported in dead code: bpo-37500."""
        cases = [
            "if 0: return",
            "class C:\n    if 0: return",
            "if 0: return\nelse:  x=1",
            "if 1: pass\nelse: return",
            "while 0: return",
            "class C:\n  if 0: return",
            "class C:\n  while 0: return",
            "class C:\n  while 0: return\n  else:  x=1",
            "class C:\n  if 0: return\n  else: x= 1",
            "class C:\n  if 1: pass\n  else: return",
        ]

        for case in cases:
            with self.subTest(case):
                with self.assertRaisesRegex(SyntaxError, "outside function"):
                    self.compile(case)

    def test_break_outside_loop_dead_code(self):
        """Break syntax errors are still reported in dead code: bpo-37500."""
        cases = [
            "if 0: break",
            "if 0: break\nelse:  x=1",
            "if 1: pass\nelse: break",
            "class C:\n  if 0: break",
            "class C:\n  if 1: pass\n  else: break",
        ]
        for case in cases:
            with self.subTest(case):
                with self.assertRaisesRegex(SyntaxError, "outside loop"):
                    self.compile(case)

    def test_continue_outside_loop_dead_code(self):
        """Continue syntax errors are still reported in dead code: bpo-37500."""
        cases = [
            "if 0: continue",
            "if 0: continue\nelse:  x=1",
            "if 1: pass\nelse: continue",
            "class C:\n  if 0: continue",
            "class C:\n  if 1: pass\n  else: continue",
        ]
        for case in cases:
            with self.subTest(case):
                with self.assertRaisesRegex(SyntaxError, "not properly in loop"):
                    self.compile(case)

    def test_jump_offsets(self):
        codestr = """
        def f(a):
            return g(i for i in x if i not in j)
        """
        self._check(codestr)

    def test_jump_forward(self):
        codestr = """
        def f():
            if yes:
                for c in a:
                    print(c)
            elif no:
                for c in a.d():
                    print(c)
        """
        self._check(codestr)

    def test_with_setup(self):
        codestr = """
        def _read_output(commandstring):
            import contextlib
            try:
                import tempfile
                fp = tempfile.NamedTemporaryFile()
            except ImportError:
                fp = open("/tmp/_osx_support.%s"%(
                    os.getpid(),), "w+b")

            with contextlib.closing(fp) as fp:
                cmd = "%s 2>/dev/null >'%s'" % (commandstring, fp.name)
                return fp.read().decode('utf-8').strip() if not os.system(cmd) else None
        """
        self._check(codestr)

    def test_try_finally_return(self):
        codestr = """
        def f():
            try:
                a
            finally:
                return 42
        """
        self._check(codestr)

    def test_break_in_false_loop(self):
        codestr = """
        def break_in_while():
            while False:
                break
        """
        self._check(codestr)

    def test_true_loop_lineno(self):
        codestr = """
            while True:
                b
        """
        self._check(codestr)

    def test_syntax_error_rebind_comp_iter_nonlocal(self):
        with self.assertRaisesRegex(
            SyntaxError,
            "comprehension inner loop cannot rebind assignment expression target 'j'",
        ):
            self.compile("[i for i in range(5) if (j := 0) for j in range(5)]")

    def test_syntax_error_rebind_comp_iter(self):
        with self.assertRaisesRegex(
            SyntaxError,
            "assignment expression cannot rebind comprehension iteration variable 'x'",
        ):
            self.compile("[x:=42 for x in 'abc']")

    def test_syntax_error_assignment_expr_in_comp_iterable(self):
        with self.assertRaisesRegex(
            SyntaxError,
            "assignment expression cannot be used in a comprehension iterable expression",
        ):
            self.compile("[x for x in (x:='abc')]")

    def test_syntax_error_assignment_expr_in_class_comp(self):
        code = """
        class C:
            [y:=42 for x in 'abc']
        """
        with self.assertRaisesRegex(
            SyntaxError,
            "assignment expression within a comprehension cannot be used in a class body",
        ):
            self.compile(code)
