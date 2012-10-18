# Copyright: Damien Elmes <anki@ichi2.net>
# -*- coding: utf-8 -*-
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from anki import consts
from anki.lang import _
from anki.utils import isWin, isMac
from aqt.qt import QDialog, QDialogButtonBox, Qt, SIGNAL
from aqt.utils import askUser, openHelp, showWarning
import aqt


class DeckConf(QDialog):

    def __init__(self, mw, first=False, search="", deck=None):
        QDialog.__init__(self, mw)
        self.mw = mw
        self.deck = deck or self.mw.col.decks.current()
        # context-sensitive extras like deck:foo
        self.search = search
        self.form = aqt.forms.dyndconf.Ui_Dialog()
        self.form.setupUi(self)
        if first:
            label = _("Build")
        else:
            label = _("Rebuild")
        self.ok = self.form.buttonBox.addButton(
            label, QDialogButtonBox.AcceptRole)
        self.mw.checkpoint(_("Options"))
        self.setWindowModality(Qt.WindowModal)
        self.connect(self.form.buttonBox,
                     SIGNAL("helpRequested()"),
                     lambda: openHelp("filtered"))
        self.setWindowTitle(_("Options for %s") % self.deck['name'])
        self.setupExamples()
        self.setupOrder()
        self.loadConf()
        self.show()
        if first:
            if isMac or isWin:
                self.form.examples.showPopup()
            else:
                mw.progress.timer(200, self.form.examples.showPopup, False)
        self.exec_()

    def setupOrder(self):
        self.form.order.addItems(consts.dynOrderLabels().values())

    def setupExamples(self):

        def onChange(*args):
            if self.ignoreChange:
                return
            f.examples.setCurrentIndex(0)

        f = self.form
        d = self.dynExamples = consts.dynExamples()
        for c, row in enumerate(d):
            if not row:
                f.examples.insertSeparator(c)
            else:
                f.examples.addItem(row[0])
        self.connect(f.examples, SIGNAL("activated(int)"),
                     self.onExample)
        # we'll need to reset whenever something is changed
        self.ignoreChange = False
        c = self.connect
        c(f.steps, SIGNAL("textEdited(QString)"), onChange)
        c(f.search, SIGNAL("textEdited(QString)"), onChange)
        c(f.order, SIGNAL("activated(int)"), onChange)
        c(f.limit, SIGNAL("valueChanged(int)"), onChange)
        c(f.stepsOn, SIGNAL("stateChanged(int)"), onChange)
        c(f.resched, SIGNAL("stateChanged(int)"), onChange)

    def onExample(self, idx):
        if idx == 0:
            return
        p = self.dynExamples[idx][1]
        f = self.form
        self.ignoreChange = True
        search = [p['search']]
        if self.search:
            search.append(self.search)
        f.search.setText(" ".join(search))
        f.order.setCurrentIndex(p['order'])
        f.resched.setChecked(p.get("resched", True))
        if p.get("steps"):
            f.steps.setText(p['steps'])
            f.stepsOn.setChecked(True)
        else:
            f.steps.setText("1 10")
            f.stepsOn.setChecked(False)
        f.limit.setValue(1000)
        self.ignoreChange = False

    def loadConf(self):
        f = self.form
        d = self.deck
        search, limit, order = d['terms'][0]
        f.search.setText(search)
        if d['delays']:
            f.steps.setText(self.listToUser(d['delays']))
            f.stepsOn.setChecked(True)
        else:
            f.steps.setText("1 10")
            f.stepsOn.setChecked(False)
        f.resched.setChecked(d['resched'])
        f.order.setCurrentIndex(order)
        f.limit.setValue(limit)

    def saveConf(self):
        f = self.form
        d = self.deck
        d['delays'] = None
        if f.stepsOn.isChecked():
            steps = self.userToList(f.steps)
            if steps:
                d['delays'] = steps
        else:
            d['delays'] = None
        d['terms'][0] = [f.search.text(),
                         f.limit.value(),
                         f.order.currentIndex()]
        d['resched'] = f.resched.isChecked()
        self.mw.col.decks.save(d)
        return True

    def reject(self):
        self.ok = False
        QDialog.reject(self)

    def accept(self):
        if not self.saveConf():
            return
        if not self.mw.col.sched.rebuildDyn():
            if askUser(_("""\
The provided search did not match any cards. Would you like to revise \
it?""")):
                return
        self.mw.reset()
        QDialog.accept(self)

    # Step load/save - fixme: share with std options screen
    ########################################################

    def listToUser(self, l):
        return " ".join([str(x) for x in l])

    def userToList(self, w, minSize=1):
        items = unicode(w.text()).split(" ")
        ret = []
        for i in items:
            if not i:
                continue
            try:
                i = float(i)
                assert i > 0
                if i == int(i):
                    i = int(i)
                ret.append(i)
            except:
                # invalid, don't update
                showWarning(_("Steps must be numbers."))
                return
        if len(ret) < minSize:
            showWarning(_("At least one step is required."))
            return
        return ret
