from collections import namedtuple
import random

from PySide6.QtCore import QAbstractProxyModel, QModelIndex, Qt
from PySide6.QtSql import QSqlTableModel
from PySide6.QtWidgets import QWidget


GROUP_ITEM = namedtuple("groupItem", ["name", "children", "index"])
ROW_ITEM = namedtuple("rowItem", ["groupIndex", "random"])


class ProcessModel(QAbstractProxyModel):
    def __init__(self, parent: QWidget, settings: dict):
        super().__init__(parent)
        self.settings = settings

        self._root_item = QModelIndex()
        self._parent_id_tuples = []  # list of groupItems
        self._parent_id_internal_indices_dict = {}  # map of group names to group indexes
        self._parent_id_internal_indices_list = []  # list of groupIndexes for locating group row
        self._source_rows = []  # map of source rows to group index
        self._column_id = 0  # id column = 'id'
        self._column_parent_id = 1  # parent_id column = 'parent_id'
        self._column_type_id = 2  # type_id column = 'type_id'
        self._column_parent_type_id = 3  # parent_type_id column = 'parent_type_id'
        self._column_order_id = 4  # order_id column = 'order_id'

        source_model = QSqlTableModel(parent, self.settings['connection'])
        source_model.setTable('operations')
        source_model.setEditStrategy(QSqlTableModel.EditStrategy.OnManualSubmit)
        source_model.setFilter(f"process_version_id = {self.settings['process_version_id']}")
        source_model.select()
        super().setSourceModel(source_model)

        # connect signals
        self.sourceModel().columnsAboutToBeInserted.connect(self.columnsAboutToBeInserted.emit)
        self.sourceModel().columnsInserted.connect(self.columnsInserted.emit)
        self.sourceModel().columnsAboutToBeRemoved.connect(self.columnsAboutToBeRemoved.emit)
        self.sourceModel().columnsRemoved.connect(self.columnsRemoved.emit)

        self.sourceModel().rowsInserted.connect(self._rowsInserted)
        self.sourceModel().rowsRemoved.connect(self._rowsRemoved)
        self.sourceModel().dataChanged.connect(self._dataChanged)

        # set grouping
        self.beginResetModel()
        source_model: QSqlTableModel = self.sourceModel()
        source_row_count = source_model.rowCount(QModelIndex())
        for row in range(source_row_count):
            parent_id_index = self.createIndex(row, self._column_parent_id, 0)
            type_id_index = self.createIndex(row, self._column_type_id, 0)
            parent_id = source_model.data(parent_id_index, Qt.DisplayRole)
            type_id = int(source_model.data(type_id_index, Qt.DisplayRole))
            parent_id_index = self._get_parent_id_index(parent_id)
            row_item = ROW_ITEM(parent_id_index, type_id)
            idx_row = parent_id_index.row()
            self._parent_id_tuples[idx_row].children.append(row_item)
            self._source_rows.append(row_item)
        self.endResetModel()

    def rowCount(self, parent: QModelIndex) -> int:
        if parent == self._root_item:
            # root level
            return len(self._parent_id_tuples)
        elif parent.internalPointer() == self._root_item:
            # children level
            return len(self._parent_id_tuples[parent.row()].children)
        else:
            return 0

    def columnCount(self, parent: QModelIndex) -> int:
        """Returns the number of columns for the children of the given parent."""
        if self.sourceModel():
            return self.sourceModel().columnCount(QModelIndex())
        else:
            return 0

    def index(self, row: int, column: int, parent: QModelIndex) -> QModelIndex:
        if parent == self._root_item:
            # this is a group
            return self.createIndex(row, column, self._root_item)
        elif parent.internalPointer() == self._root_item:
            return self.createIndex(row, column, self._parent_id_tuples[parent.row()].index)
        else:
            return QModelIndex()

    def parent(self, index) -> QModelIndex:
        parent = index.internalPointer()
        if parent == self._root_item:
            return self._root_item
        else:
            parent_row = self._getGroupRow(parent)
            return self.createIndex(parent_row, 0, self._root_item)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            parent = index.internalPointer()
            if parent == self._root_item:
                return self._parent_id_tuples[index.row()].name
            else:
                parent_row = self._getGroupRow(parent)
                source_row = self._source_rows.index(self._parent_id_tuples[parent_row].children[index.row()])
                source_index = self.createIndex(source_row, index.column(), 0)
                return self.sourceModel().data(source_index, role)
        return None

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        return self.sourceModel().headerData(section, orientation, role)

    def mapToSource(self, index):
        if not index.isValid():
            return QModelIndex()

        parent = index.internalPointer()
        if not parent.isValid():
            return QModelIndex()
        elif parent == self._root_item:
            return QModelIndex()
        else:
            row_item_ = self._parent_id_tuples[parent.row()].children[index.row()]
            source_row = self._source_rows.index(row_item_)
            return self.createIndex(source_row, index.column(), QModelIndex())

    def mapFromSource(self, index):
        row_item_ = self._source_rows[index.row()]
        group_row = self._getGroupRow(row_item_.groupIndex)
        item_row = self._parent_id_tuples[group_row].children.index(row_item_)
        return self.createIndex(item_row, index.column(), self._parent_id_internal_indices_list[group_row])

    def _get_parent_id_index(self, parent_id):
        """ return the index for a group denoted with name.
        if there is no group with given name, create and then return"""
        if parent_id in self._parent_id_internal_indices_dict:
            return self._parent_id_internal_indices_dict[parent_id]
        else:
            parent_id_row = len(self._parent_id_internal_indices_dict)
            parent_id_internal_index = self.createIndex(parent_id_row, 0, self._root_item)
            self._parent_id_internal_indices_dict[parent_id] = parent_id_internal_index
            self._parent_id_internal_indices_list.append(parent_id_internal_index)
            self._parent_id_tuples.append(GROUP_ITEM(parent_id, [], parent_id_internal_index))
            self.layoutChanged.emit()
            return parent_id_internal_index

    def _getGroupRow(self, group_index):
        for i, x in enumerate(self._parent_id_internal_indices_list):
            if id(group_index) == id(x):
                return i
        return 0

    def _rowsInserted(self, parent, start, end):
        for row in range(start, end+1):
            group_name = self.sourceModel().data(self.createIndex(row, self._column_parent_id, 0), Qt.DisplayRole)
            group_index = self._get_parent_id_index(group_name)
            self._getGroupRow(group_index)
            group_item_ = self._parent_id_tuples[self._getGroupRow(group_index)]
            row_item_ = ROW_ITEM(group_index, random.random())
            group_item_.children.append(row_item_)
            self._source_rows.insert(row, row_item_)
        self.layoutChanged.emit()

    def _rowsRemoved(self, parent, start, end):
        for row in range(start, end+1):
            row_item_ = self._source_rows[start]
            group_index = row_item_.groupIndex
            group_item_ = self._parent_id_tuples[self._getGroupRow(group_index)]
            children_row = group_item_.children.index(row_item_)
            group_item_.children.pop(children_row)
            self._source_rows.pop(start)
            if not len(group_item_.children):
                # remove the group
                group_row = self._getGroupRow(group_index)
                group_name = self._parent_id_tuples[group_row].name
                self._parent_id_tuples.pop(group_row)
                self._parent_id_internal_indices_list.pop(group_row)
                del self._parent_id_internal_indices_dict[group_name]
        self.layoutChanged.emit()

    def _dataChanged(self, topLeft, bottomRight):
        top_row = topLeft.row()
        bottom_row = bottomRight.row()
        source_model = self.sourceModel()
        # loop through all the changed data
        for row in range(top_row,bottom_row+1):
            old_group_index = self._source_rows[row].groupIndex
            old_group_item = self._parent_id_tuples[self._getGroupRow(old_group_index)]
            new_group_name = source_model.data(self.createIndex(row, self._column_parent_id, 0), Qt.DisplayRole)
            if new_group_name != old_group_item.name:
                # move to new group...
                new_group_index = self._get_parent_id_index(new_group_name)
                new_group_item = self._parent_id_tuples[self._getGroupRow(new_group_index)]

                row_item_ = self._source_rows[row]
                new_group_item.children.append(row_item_)

                # delete from old group
                old_group_item.children.remove(row_item_)
                if not len(old_group_item.children):
                    # remove the group
                    group_row = self._getGroupRow(old_group_item.index)
                    group_name = old_group_item.name
                    self._parent_id_tuples.pop(group_row)
                    self._parent_id_internal_indices_list.pop(group_row)
                    del self._parent_id_internal_indices_dict[group_name]

        self.layoutChanged.emit()
