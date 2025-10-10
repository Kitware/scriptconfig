import ubelt as ub
import scriptconfig as scfg
from collections import defaultdict


def test_modal_fuzzy_hyphens():
    import pytest
    pytest.skip('does not work yet')

    callnums = defaultdict(lambda: 0)

    class _TestCommandTemplate(scfg.DataConfig):
        # not a normal pattern, just make tests more concise.
        __command__ = '_base_'
        common_option = scfg.Flag(None, help='an option with an underscore')

        @classmethod
        def main(cls, argv=1, **kwargs):
            self = cls.cli(argv=argv, data=kwargs)
            callnums[cls.__command__] += 1
            print(f'Called {cls.__command__} with: ' + str(self))

        def _parserkw(self):
            return super()._parserkw() | {'exit_on_error': False}

    class Do_Command1(_TestCommandTemplate):
        __command__ = 'do_command1'
        __aliases__ = ['do-command1']

    class Do_Command2(_TestCommandTemplate):
        __command__ = 'do_command2'
        __aliases__ = ['do-command2']

    class Do_Command3(_TestCommandTemplate):
        __command__ = 'do_command3'
        __aliases__ = ['do-command3']

    class Do_Command4(_TestCommandTemplate):
        __command__ = 'do_command4'
        __aliases__ = ['do-command4']

    class TestSubModalCLI(scfg.ModalCLI):
        """
        Second level modal CLI
        """
        __version__ = '4.5.6'
        __command__ = 'sub_modal'
        __aliases__ = ['sub-modal']
        __subconfigs__ = [
            Do_Command3,
            Do_Command4,
        ]

        def _parserkw(self):
            return super()._parserkw() | {'exit_on_error': False}

    class TestModalCLI(scfg.ModalCLI):
        """
        Top level modal CLI
        """
        __version__ = '1.2.3'
        __subconfigs__ = [
            Do_Command1,
            Do_Command2,
            TestSubModalCLI,
        ]

        def _parserkw(self):
            return super()._parserkw() | {'exit_on_error': False}

    try:
        TestModalCLI.main(argv=['--help'])
    except SystemExit:
        print('prevent system exit due to calling --help')

    try:
        TestModalCLI.main(argv=['sub_modal', '--help'])
    except SystemExit:
        print('prevent system exit due to calling --help')

    # Run with different variants of fuzzy hyphens

    TestModalCLI.main(argv=['sub_modal', '--version'])

    TestModalCLI.main(argv=['do_command1', '--common_option'])
    TestModalCLI.main(argv=['do_command1', '--common-option'])
    TestModalCLI.main(argv=['do_command2'])

    TestModalCLI.main(argv=['sub_modal', 'do_command3'])
    TestModalCLI.main(argv=['sub_modal', 'do_command4', '--common_option'])
    TestModalCLI.main(argv=['sub_modal', 'do_command4', '--common-option'])

    # Use hyphens in the modal commands
    print('NEW STUFF')
    TestModalCLI.main(argv=['do-command1'])

    TestModalCLI.main(argv=['sub_modal', 'do-command4', '--common-option=3'])
    TestModalCLI.main(argv=['sub-modal', 'do-command4', '--common-option=4'])

    print(f'callnums = {ub.urepr(callnums, nl=1)}')


def test_modal_customize_command_classlevel():
    class MyModalCLI(scfg.ModalCLI):
        ...

    @MyModalCLI.register(command='command1')
    class Command1(scfg.DataConfig):
        __alias__ = ['alias1']  # should be used because alias not given in the decorator
        foo = scfg.Value('spam', help='spam spam spam spam')

        @classmethod
        def main(cls, argv=1, **kwargs):
            cls.cli(argv=argv, data=kwargs, verbose=True)

    @MyModalCLI.register(command='command2', alias=['alias2', 'alias3'])
    class Command2(scfg.DataConfig):
        bar = 'biz'
        __alias__ = ['overwritten']  # wil not be used because alias is given in the decorator

        @classmethod
        def main(cls, argv=1, **kwargs):
            cls.cli(argv=argv, data=kwargs, verbose=True)

    with ub.CaptureStdout(suppress=True) as cap:
        MyModalCLI.main(argv=['--help'], _noexit=True)
    assert 'command1' in cap.text
    assert 'command2' in cap.text
    assert 'alias2' in cap.text
    assert 'alias3' in cap.text
    assert 'alias1' in cap.text
    assert 'overwritten' not in cap.text
    assert 'Command1' not in cap.text
    assert 'Command2' not in cap.text

    assert MyModalCLI.main(argv=['command1']) == 0
    assert MyModalCLI.main(argv=['command2']) == 0


def test_modal_customize_command_instancelevel():
    class MyModalCLI(scfg.ModalCLI):
        ...

    modal = MyModalCLI()

    @modal.register(command='command1')
    class Command1(scfg.DataConfig):
        __alias__ = 'alias1'
        foo = scfg.Value('spam', help='spam spam spam spam')
        @classmethod
        def main(cls, argv=1, **kwargs):
            cls.cli(argv=argv, data=kwargs, verbose=True)

    @modal.register(command='command2', alias=['alias2', 'alias3'])
    class Command2(scfg.DataConfig):
        __alias__ = ['overwritten']
        bar = 'biz'
        @classmethod
        def main(cls, argv=1, **kwargs):
            cls.cli(argv=argv, data=kwargs, verbose=True)

    with ub.CaptureStdout(suppress=0) as cap:
        modal.main(argv=['--help'], _noexit=True)
    assert 'command1' in cap.text
    assert 'command2' in cap.text
    assert 'alias2' in cap.text
    assert 'alias3' in cap.text
    assert 'alias1' in cap.text
    assert 'overwritten' not in cap.text
    assert 'Command1' not in cap.text
    assert 'Command2' not in cap.text

    assert modal.main(argv=['command1']) == 0
    assert modal.main(argv=['command2']) == 0


def test_customized_modals():
    """
    We should be able to reuse the same subconfig in different modals but
    have them be under different commands.
    """

    class Modal1(scfg.ModalCLI):
        ...

    class Modal2(scfg.ModalCLI):
        ...

    modal1 = Modal1()
    modal2 = Modal2()

    class Command1(scfg.DataConfig):
        foo = scfg.Value('spam', help='spam spam spam spam')
        @classmethod
        def main(cls, argv=1, **kwargs):
            cls.cli(argv=argv, data=kwargs, verbose=True)

    modal1.register(Command1, command='command1')
    modal2.register(Command1, command='action1')

    with ub.CaptureStdout(suppress=0) as cap:
        try:
            modal1.main(argv=['--help'])
        except SystemExit:
            ...
        else:
            raise AssertionError('should have exited')
    assert 'command1' in cap.text
    assert 'action1' not in cap.text

    with ub.CaptureStdout(suppress=0) as cap:
        modal2.main(argv=['--help'], _noexit=True)
    assert 'command1' not in cap.text
    assert 'action1' in cap.text


def test_submodals():
    """
    We should be able to reuse the same subconfig in different modals but
    have them be under different commands.

    CommandLine:
        xdoctest -m tests/test_modal.py test_submodals
    """
    import scriptconfig as scfg

    class Modal1(scfg.ModalCLI):
        ...

    class Modal2(scfg.ModalCLI):
        ...

    class Modal3(scfg.ModalCLI):
        ...

    class Command(scfg.DataConfig):
        __command__ = 'command'
        foo = scfg.Value('spam', help='spam spam spam spam')
        @classmethod
        def main(cls, argv=1, **kwargs):
            cls.cli(argv=argv, data=kwargs, verbose=True)

    Modal3.register(Command, command='command4')
    Modal2.register(Modal3, command='modal3')
    Modal2.register(Command, command='command3')
    Modal1.register(Modal2, command='modal2')
    Modal1.register(Command, command='command1')
    Modal1.register(Command, command='command2')

    with ub.CaptureStdout(suppress=0) as cap:
        Modal1.main(argv=['--help'], _noexit=True)
    assert 'modal2' in cap.text
    with ub.CaptureStdout(suppress=0) as cap:
        Modal1.main(argv=['modal2', '--help'], _noexit=True)
    assert 'modal3' in cap.text
    with ub.CaptureStdout(suppress=0) as cap:
        Modal1.main(argv=['command1', '--help'], _noexit=True)
    assert 'foo' in cap.text
    with ub.CaptureStdout(suppress=0) as cap:
        Modal1.main(argv=['modal2', 'modal3', '--help'], _noexit=True)
    assert 'command4' in cap.text
    with ub.CaptureStdout(suppress=0) as cap:
        Modal1.main(argv=['modal2', 'command3', '--help'], _noexit=True)
    assert 'foo' in cap.text

    assert Modal1.main(argv=['command1']) == 0

    # What happens when modals are given no args?
    with ub.CaptureStdout(suppress=0) as cap:
        try:
            Modal1.main(argv=[])
        except ValueError as ex:
            assert 'no command given' in str(ex)
        else:
            assert False
    assert 'modal2' in cap.text

    with ub.CaptureStdout(suppress=0) as cap:
        try:
            Modal1.main(argv=['modal2'])
        except ValueError as ex:
            assert 'no command given' in str(ex)
        else:
            assert False
    assert 'modal3' in cap.text

    with ub.CaptureStdout(suppress=0) as cap:
        try:
            Modal1.main(argv=['modal2', 'modal3'])
        except ValueError as ex:
            assert 'no command given' in str(ex)
        else:
            assert False
    assert 'command4' in cap.text


def test_modal_version():
    """
    Modal CLIs should be able to cause the version to print

    CommandLine:
        xdoctest -m tests/test_modal.py test_submodals
    """
    import scriptconfig as scfg
    from scriptconfig import diagnostics
    diagnostics.DEBUG_MODAL = 1

    class Modal1(scfg.ModalCLI):
        __version__ = '1.1.1'

        class Modal2(scfg.ModalCLI):
            __version__ = '2.2.2'

            class Modal3(scfg.ModalCLI):
                __version__ = '3.3.3'

    with ub.CaptureStdout(suppress=0) as cap:
        Modal1.main(argv=['--version'])
    assert '1.1.1' in cap.text

    with ub.CaptureStdout(suppress=0) as cap:
        Modal1.main(argv=['Modal2', '--version'])
    assert '2.2.2' in cap.text

    with ub.CaptureStdout(suppress=0) as cap:
        Modal1.main(argv=['Modal2', 'Modal3', '--version'])
    assert '3.3.3' in cap.text


if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/scriptconfig/tests/test_modal.py
    """
    test_modal_fuzzy_hyphens()
