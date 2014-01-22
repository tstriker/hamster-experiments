# - coding: utf-8 -

# Copyright (c) 2011-2012 Media Modifications, Ltd.
# Dual licensed under the MIT or GPL Version 2 licenses.
from gi.repository import GObject as gobject

class TreeModel(gobject.GObject):
    """A helper structure that is used by treeviews and listitems - our version
        of a tree model, based on list.
        Pass in either simple list for single-column data or a nested list for
        multi-column
    """

    __gsignals__ = {
        "row-changed": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        "row-deleted": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        "row-inserted": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
    }

    def __init__(self, iterable = None):
        # we will wrap every row in an object that will listen to setters and getters. can't go beyond that though
        # which means data[row][col]['imagine we have a dictionary here so this is a key'] = 'a' will go by unnoticed!
        # is that ok? - TODO

        self._data = []

        gobject.GObject.__init__(self)
        if iterable:
            self.extend(iterable)

    def __setitem__(self, row_idx, val):
        self._data.__setitem__(row_idx, TreeModelRow(self, val))
        self._on_row_changed(self._data[row_idx]._row)

    def __getitem__(self, row_idx):
        return self._data.__getitem__(row_idx)

    def __delitem__(self, idx):
        del self._data[idx]
        self._on_row_deleted()

    def __len__(self):
        return len(self._data)

    def index(self, item):
        return self._data.index(item)

    def append(self, row):
        if isinstance(row, list) == False:
            row = [row]
        self._data.append(TreeModelRow(self, row))
        self._on_row_changed(None)

    def remove(self, target_row):
        """remove the given row"""
        if target_row in self._data:
            self.__delitem__(self._data.index(target_row))
        else:
            # TODO - figure out a better way
            if isinstance(target_row, list) == False:
                target_row = [target_row]

            for i, row in enumerate(self._data):
                if row._row == target_row:
                    self.__delitem__(i)
                    return

    def pop(self, idx):
        row = self._data.pop(idx)
        self._on_row_deleted()
        return row

    def insert(self, i, row):
        if isinstance(row, list) == False:
            row = [row]
        self._data.insert(i, TreeModelRow(self, row))
        self._on_row_changed(None)

    def extend(self, rows):
        for row in rows:
            if isinstance(row, list) == False:
                row = [row]
            self._data.append(TreeModelRow(self, row))
        self._on_row_changed(None)

    def _on_row_changed(self, row = None, col = None):
        self.emit("row-changed", self._data.index(row) if row else None)

    def _on_row_deleted(self):
        self.emit("row-deleted")


class TreeModelRow(object):
    def __init__(self, parent = None, row = None):
        self._parent = parent

        if hasattr(row, "__getitem__") == False:
            row = [row]

        self._row = row or []

    def __setitem__(self, col, val):
        self._row[col] = val
        self._parent._on_row_changed(self, col)

    def __getitem__(self, col):
        return self._row[col]

    def __iter__(self):
        return iter(self._row)

    def __repr__(self):
        return "<TreeModelRow %s %s>" % (getattr(self, "id", None) or str(id(self)), str(self._row))
