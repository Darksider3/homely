from homely._errors import HelperError
from homely._engine2 import Helper, Cleaner, getengine
from homely._utils import haveexecutable
from homely._ui import isinteractive, system


def pipinstall(packagename, pips=[], *, trypips=[]):
    engine = getengine()
    for pip in pips:
        helper = PIPInstall(packagename, pip, mustinstall=True)
        engine.run(helper)
    for pip in trypips:
        helper = PIPInstall(packagename, pip, mustinstall=False)
        engine.run(helper)


_known_pips = {}


def _haspkg(pipcmd, name):
    output = system([pipcmd, 'list', '--disable-pip-version-check'],
                    stdout=True)[1]
    find = '%s ' % name
    for line in output.decode('utf-8').split("\n"):
        if line.startswith(find):
            return True
    return False


class PIPInstall(Helper):
    _name = None
    _pip = None
    _pipcmd = None
    _mustinstall = True
    # TODO: get rid of this option
    _user = False

    def __init__(self, name, pip, mustinstall):
        super(PIPInstall, self).__init__()
        self._name = name
        self._mustinstall = mustinstall
        self._pip = pip

        try:
            haveexec = _known_pips[pip]
        except KeyError:
            haveexec = haveexecutable(pip)
            _known_pips[pip] = haveexec

        if haveexec:
            self._pipcmd = pip

    def getcleaner(self):
        if self._pipcmd is not None:
            return PIPCleaner(self._name, self._pipcmd)

    def pathsownable(self):
        return {}

    def getclaims(self):
        yield "%s:%s" % (self._pipcmd, self._name)

    def isdone(self):
        if self._pipcmd is None:
            if not self._mustinstall:
                return True
            raise HelperError("%s executable not found" % self._pipcmd)
        return _haspkg(self._pipcmd, self._name)

    @property
    def description(self):
        return "%s install --user %s" % (self._pipcmd, self._name)

    def makechanges(self):
        if self._pipcmd is None:
            raise HelperError("%s executable not found" % self._pipcmd)
        cmd = [
            self._pipcmd,
            'install',
            self._name,
            '--user',
            '--disable-pip-version-check',
        ]
        system(cmd)
        factname = 'pipinstall:%s:%s' % (self._pipcmd, self._name)
        self._setfact(factname, True)

    def affectspath(self, path):
        return False


class PIPCleaner(Cleaner):
    def __init__(self, name, pipcmd):
        super(PIPCleaner, self).__init__()
        self._name = name
        self._pipcmd = pipcmd

    def asdict(self):
        return dict(name=self._name, pipcmd=self._pipcmd)

    @classmethod
    def fromdict(class_, data):
        return class_(data["name"], data["pipcmd"])

    def __eq__(self, other):
        return self._name == other._name and self._pipcmd == other._pipcmd

    def isneeded(self):
        factname = 'pipinstall:%s:%s' % (self._pipcmd, self._name)
        hasfact = self._getfact(factname, False)
        return hasfact and _haspkg(self._pipcmd, self._name)

    @property
    def description(self):
        return "%s uninstall %s" % (self._pipcmd, self._name)

    def makechanges(self):
        cmd = [
            self._pipcmd,
            'uninstall',
            self._name,
            '--disable-pip-version-check',
        ]
        if not isinteractive():
            cmd.append('--yes')
        factname = 'pipinstall:%s:%s' % (self._pipcmd, self._name)
        try:
            system(cmd)
        finally:
            self._clearfact(factname)
        return []

    def needsclaims(self):
        yield "%s:%s" % (self._pipcmd, self._name)

    def wantspath(self, path):
        return False
