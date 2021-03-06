# Copyright: Damien Elmes <anki@ichi2.net>
# -*- coding: utf-8 -*-
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from aqt.qt import *
import aqt.editor
from aqt.utils import saveGeom, restoreGeom
from anki.hooks import addHook, remHook

class EditCurrent(QDialog):

    def __init__(self, mw):
        QDialog.__init__(self, mw)
        self.mw = mw
        self.form = aqt.forms.editcurrent.Ui_Dialog()
        self.form.setupUi(self)
        self.setWindowTitle(_("Edit Current"))
        self.setMinimumHeight(400)
        self.setMinimumWidth(500)
        self.connect(self.form.buttonBox.button(QDialogButtonBox.Save),
                     SIGNAL("clicked()"),
                     self.onSave)
        self.connect(self,
                     SIGNAL("rejected()"),
                     self.onSave)
        self.editor = aqt.editor.Editor(self.mw, self.form.fieldsArea, self)
        self.editor.setNote(self.mw.reviewer.card.note())
        restoreGeom(self, "editcurrent")
        addHook("reset", self.onReset)
        self.mw.requireReset()
        self.show()
        # reset focus after open
        self.editor.web.setFocus()

    def onReset(self):
        # lazy approach for now: throw away edits
        n = self.mw.reviewer.card.note()
        n.load()
        self.editor.setNote(n)

    def onSave(self):
        remHook("reset", self.onReset)
        self.editor.saveNow()
        self.editor.setNote(None)
        r = self.mw.reviewer
        try:
            r.card.load()
        except TypeError:
            # card was removed by clayout
            pass
        else:
            self.mw.reviewer.cardQueue.append(self.mw.reviewer.card)
        self.mw.moveToState("review")
        saveGeom(self, "editcurrent")
