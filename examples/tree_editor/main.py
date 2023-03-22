# Copyright (C) 2022 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

# Editable Tree Model Example
# https://doc.qt.io/qtforpython/examples/example_widgets_itemviews_editabletreemodel.html
# https://code.qt.io/cgit/qt/qtbase.git/tree/examples/widgets/itemviews/editabletreemodel?h=6.4
# https://doc.qt.io/qt-6/qtwidgets-itemviews-editabletreemodel-example.html#treemodel-setupmodeldata


import sys
from pathlib import Path


from PySide6.QtWidgets import \
    QApplication, QVBoxLayout, QGroupBox, QPushButton, QHBoxLayout, QSpacerItem, QSizePolicy, \
    QDataWidgetMapper, QFormLayout, QLabel, QLineEdit
from PySide6.QtCore import QAbstractItemModel, QItemSelectionModel, QModelIndex, Qt, Slot
from PySide6.QtWidgets import QAbstractItemView, QMainWindow, QTreeView, QWidget
from PySide6.QtTest import QAbstractItemModelTester

from librarymodel import LibraryModel
from processmodel import ProcessModel


class MainWindowUi:
    def __init__(self, main_window: QMainWindow):
        main_window.setWindowTitle("Editable Tree Model")
        main_window.resize(2000, 1000)

        # -----------------------------------------------------------
        # LEFT LAYOUT: LIBRARY OF OPERATION TYPES (TREE VIEW)
        # -----------------------------------------------------------

        self.library_view = QTreeView(main_window)

        library_layout = QVBoxLayout()
        library_layout.addWidget(self.library_view)

        self.library_group_box = QGroupBox('Library', main_window)
        self.library_group_box.setLayout(library_layout)

        # ---------------------------------------------
        # MIDDLE LAYOUT: PROCESS (TREE VIEW)
        # ---------------------------------------------

        self.button_insert_row = QPushButton('Insert row', main_window)
        self.button_insert_column = QPushButton('Insert column', main_window)
        self.button_remove_row = QPushButton('Remove row', main_window)
        self.button_remove_column = QPushButton('Remove column', main_window)
        self.button_insert_child = QPushButton('Insert child', main_window)
        self.button_change_type = QPushButton('Change type', main_window)

        process_editor_buttons_layout = QHBoxLayout()
        process_editor_buttons_layout.addWidget(self.button_insert_row)
        process_editor_buttons_layout.addWidget(self.button_insert_column)
        process_editor_buttons_layout.addItem(QSpacerItem(1, 1, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        process_editor_buttons_layout.addWidget(self.button_remove_row)
        process_editor_buttons_layout.addWidget(self.button_remove_column)
        process_editor_buttons_layout.addItem(QSpacerItem(1, 1, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        process_editor_buttons_layout.addWidget(self.button_insert_child)
        process_editor_buttons_layout.addItem(QSpacerItem(1, 1, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        process_editor_buttons_layout.addWidget(self.button_change_type)

        self.process_view = QTreeView()
        # self.view.setAlternatingRowColors(True)
        self.process_view.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.process_view.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.process_view.setAnimated(False)
        self.process_view.setAllColumnsShowFocus(True)

        process_editor_main_layout = QVBoxLayout()
        process_editor_main_layout.addLayout(process_editor_buttons_layout)
        process_editor_main_layout.addWidget(self.process_view)

        self.process_editor_group_box = QGroupBox('Process', main_window)
        self.process_editor_group_box.setLayout(process_editor_main_layout)

        # -----------------------------------------------------------
        # RIGHT LAYOUT: PARAMETERS (FORM LAYOUT)
        # -----------------------------------------------------------

        parameters_buttons_layout = QHBoxLayout()
        self.button_previous = QPushButton('Previous', main_window)
        self.button_next = QPushButton('Next', main_window)
        parameters_buttons_layout.addWidget(self.button_previous)
        parameters_buttons_layout.addWidget(self.button_next)
        #
        self.button_previous.setEnabled(False)

        parameters_form_layout = QFormLayout()
        self.line_edit_parameters = []
        self.label_parameters = []
        for i in range(15):
            self.line_edit_parameters.append(QLineEdit(main_window))
            self.label_parameters.append(QLabel(f'Parameter {i}', main_window))
            parameters_form_layout.addRow(self.label_parameters[i], self.line_edit_parameters[i])

        self.editor_info_view = QWidget(main_window)

        parameters_main_layout = QVBoxLayout()
        parameters_main_layout.addLayout(parameters_buttons_layout)
        parameters_main_layout.addLayout(parameters_form_layout)
        parameters_main_layout.addSpacerItem(QSpacerItem(1, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        parameters_main_layout.addWidget(self.editor_info_view)

        self.parameters_group_box = QGroupBox('Parameters', main_window)
        self.parameters_group_box.setLayout(parameters_main_layout)

        # ----------------------------------------------------------
        #                        MAIN LAYOUT
        # ----------------------------------------------------------

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.library_group_box, 3)
        main_layout.addWidget(self.process_editor_group_box, 4)
        main_layout.addWidget(self.parameters_group_box, 2)

        central_widget = QWidget(main_window)
        central_widget.setLayout(main_layout)
        main_window.setCentralWidget(central_widget)

        # ----------------------------------------------------------
        #                         MENU BAR
        # ----------------------------------------------------------

        menubar = main_window.menuBar()
        file_menu = menubar.addMenu("&File")

        self.exit_action = file_menu.addAction("E&xit")
        self.exit_action.setShortcut("Ctrl+Q")

        self.actions_menu = menubar.addMenu("&Actions")

        self.insert_row_action = self.actions_menu.addAction("Insert Row")
        self.insert_row_action.setShortcut("Ctrl+I, R")

        self.insert_column_action = self.actions_menu.addAction("Insert Column")
        self.insert_column_action.setShortcut("Ctrl+I, C")

        self.actions_menu.addSeparator()
        self.remove_row_action = self.actions_menu.addAction("Remove Row")
        self.remove_row_action.setShortcut("Ctrl+R, R")

        self.remove_column_action = self.actions_menu.addAction("Remove Column")
        self.remove_column_action.setShortcut("Ctrl+R, C")

        self.actions_menu.addSeparator()
        self.insert_child_action = self.actions_menu.addAction("Insert Child")
        self.insert_child_action.setShortcut("Ctrl+N")

        help_menu = menubar.addMenu("&Help")
        about_qt_action = help_menu.addAction("About Qt", qApp.aboutQt)
        about_qt_action.setShortcut("F1")


class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.ui = MainWindowUi(self)

        process_headers, positions, column_data = self.get_process_data()

        self.process_model = ProcessModel(process_headers, positions, column_data, self)
        self.library_model = LibraryModel(["Header 1", "Header 2"], self.get_library_txt(), self)

        # Create the mapper for process_model to feed data to
        self.mapper = QDataWidgetMapper()
        self.mapper.setModel(self.process_model)
        for i in range(len(self.ui.line_edit_parameters)):
            self.mapper.addMapping(self.ui.line_edit_parameters[i], i)
        self.mapper.toFirst()
        self.update_ui(self.mapper_index())

        if "-t" in sys.argv:
            QAbstractItemModelTester(self.process_model, self)
        self.ui.process_view.setModel(self.process_model)
        self.ui.process_view.expandAll()
        for column in range(1, self.process_model.columnCount()):
            self.ui.process_view.hideColumn(column)

        if "-t" in sys.argv:
            QAbstractItemModelTester(self.library_model, self)
        self.ui.library_view.setModel(self.library_model)
        self.ui.library_view.expandAll()

        for column in range(self.process_model.columnCount()):
            self.ui.process_view.resizeColumnToContents(column)

        for column in range(self.library_model.columnCount()):
            self.ui.library_view.resizeColumnToContents(column)

        process_selection_model = self.ui.process_view.selectionModel()
        process_selection_model.selectionChanged.connect(self.process_update_actions)

        self.ui.exit_action.triggered.connect(self.close)
        self.ui.actions_menu.triggered.connect(self.process_update_actions)
        self.ui.insert_row_action.triggered.connect(self.insert_row)
        self.ui.insert_column_action.triggered.connect(self.insert_column)
        self.ui.remove_row_action.triggered.connect(self.remove_row)
        self.ui.remove_column_action.triggered.connect(self.remove_column)
        self.ui.insert_child_action.triggered.connect(self.insert_child)

        self.ui.button_insert_row.clicked.connect(self.insert_row)
        self.ui.button_insert_column.clicked.connect(self.insert_column)
        self.ui.button_remove_row.clicked.connect(self.remove_row)
        self.ui.button_remove_column.clicked.connect(self.remove_column)
        self.ui.button_insert_child.clicked.connect(self.insert_child)

        self.ui.library_view.doubleClicked.connect(self.on_doubleclick_library_view)
        self.ui.process_view.clicked.connect(self.on_click_process_view)

        self.ui.button_previous.clicked.connect(self.on_click_previous)
        self.ui.button_next.clicked.connect(self.on_click_next)

        self.ui.process_view.setCurrentIndex(self.mapper_index())
        self.process_update_actions()

    @Slot()
    def on_click_previous(self):
        """
        On click 'Previous parameter' button, move to previous item of tree.
        If current row is the first row, then move up to the parent item of the branch.
        If current branch has previous row, then check if the previous row has children,
        and do movement depending on presence of children:
            if there is no child/children, then move forward to previous row of current branch;
            if there is child/children, then iterate over children and move down to the last row of last child.
        After every move update 'isEnabled' method of 'Next' and 'Previous' buttons.
        """

        if self.mapper_row() == 0:
            # move up to parent item of the branch
            parent_index: QModelIndex = self.mapper_index().parent()
            self.mapper.setRootIndex(parent_index.parent())
            self.mapper.setCurrentIndex(parent_index.row())
            self.select_row_in_process_view()
            self.update_ui(self.mapper_index())
            return

        self.mapper.toPrevious()
        while self.has_children(self.mapper_index()):
            # move inside the branch
            self.mapper.setRootIndex(self.mapper_index())
            self.mapper.toLast()
        self.select_row_in_process_view()
        self.update_ui(self.mapper_index())

    @Slot()
    def on_click_next(self):
        """
        On click 'Next parameter' button, move to next item of tree.
        if current item has children, move to first child of current item.
        If current branch has next row, move to next row of current branch.
        if current branch has no next row, move to root item of next branch.
        If current item is the last item of the tree, do nothing.
        @return:
        """

        is_allow_go_inside_branch = True
        for i in range(5):

            if is_allow_go_inside_branch and self.has_children(self.mapper_index()):
                # move inside the branch
                self.mapper.setRootIndex(self.mapper_index())
                self.mapper.toFirst()
                self.select_row_in_process_view()
                self.update_ui(self.mapper_index())
                return

            if self.mapper_row() < self.row_count(self.mapper_index()) - 1:
                # move to next row (of current branch)
                self.mapper.toNext()
                self.select_row_in_process_view()
                self.update_ui(self.mapper_index())
                return

            # move outside the branch
            parent_index: QModelIndex = self.mapper_index().parent()
            self.mapper.setRootIndex(parent_index.parent())
            self.mapper.setCurrentIndex(parent_index.row())
            is_allow_go_inside_branch = False

    def select_row_in_process_view(self):
        row = self.mapper.currentIndex()
        row_index = self.process_model.index(row, 0, self.mapper.rootIndex())
        self.ui.process_view.setCurrentIndex(row_index)

    def mapper_index(self):
        row = self.mapper.currentIndex()
        return self.process_model.index(row, 0, self.mapper.rootIndex())

    @staticmethod
    def row_count(index: QModelIndex) -> int:
        model = index.model()
        return model.get_item(index.parent()).child_count()

    def mapper_row(self):
        return self.mapper.currentIndex()

    @staticmethod
    def is_root(index: QModelIndex) -> bool:
        return index.row() == -1

    def is_last_index_of_branch(self, index: QModelIndex) -> bool:
        return index.row() == self.process_model.get_item(index.parent()).child_count() - 1

    def has_next(self, index: QModelIndex) -> bool:
        last_row = self.process_model.get_item(index.parent()).child_count() - 1
        return index.row() < last_row

    @staticmethod
    def has_children(index: QModelIndex) -> bool:
        model = index.model()
        return model.hasChildren(index)

    def is_last_item_of_tree(self, index: QModelIndex, is_first_iteration: bool = True) -> bool:
        if self.is_root(index):
            return True
        if is_first_iteration and self.has_children(index):
            return False
        if self.has_next(index):
            return False
        return self.is_last_item_of_tree(index.parent(), is_first_iteration=False)

    def is_first_item_of_tree(self, index: QModelIndex) -> bool:
        if index.row() == 0 and self.is_root(index.parent()):
            return True
        return False

    def update_ui(self, index: QModelIndex = None):
        self.ui.button_previous.setEnabled(not self.is_first_item_of_tree(index))
        self.ui.button_next.setEnabled(not self.is_last_item_of_tree(index))

        model = self.process_model
        item = model.get_item(index)
        data = item.item_data
        for column in range(len(self.ui.line_edit_parameters)):
            if column >= len(data) or data[column] is None:
                self.ui.line_edit_parameters[column].hide()
                self.ui.label_parameters[column].hide()
            else:
                self.ui.line_edit_parameters[column].show()
                self.ui.label_parameters[column].show()

    @staticmethod
    def get_process_data():
        def position(_str_):
            _pos_ = 0
            while _pos_ < len(_str_):
                if _str_[_pos_] != " ":
                    break
                _pos_ += 1
            return _pos_

        file = Path(__file__).parent / "process.txt"
        _text = file.read_text()
        _strings = _text.split("\n")

        _lists = []
        _positions = []
        for _string in _strings:
            _string = _string.rstrip()
            if _string:
                _positions.append(position(_string))
                _lists.append([_str.strip() for _str in _string.split() if isinstance(_str, str)])

        max_number_of_columns = max([len(_str) for _str in _lists])
        _headers = [f"Column {i}" for i in range(max_number_of_columns)]

        return _headers, _positions, _lists

    @staticmethod
    def get_library_txt():
        file = Path(__file__).parent / "library.txt"
        _list = file.read_text()
        return _list

    @Slot()
    def insert_child(self) -> None:
        selection_model = self.ui.process_view.selectionModel()
        index: QModelIndex = selection_model.currentIndex()
        model: QAbstractItemModel = self.ui.process_view.model()

        if model.columnCount(index) == 0:
            if not model.insertColumn(0, index):
                return

        if not model.insertRow(0, index):
            return

        for column in range(model.columnCount(index)):
            child: QModelIndex = model.index(0, column, index)
            model.setData(child, "[No data]", Qt.EditRole)
            if not model.headerData(column, Qt.Horizontal):
                model.setHeaderData(column, Qt.Horizontal, "[No header]", Qt.EditRole)

        selection_model.setCurrentIndex(model.index(0, 0, index), QItemSelectionModel.ClearAndSelect)
        self.process_update_actions()

    @Slot()
    def insert_column(self) -> None:
        model: QAbstractItemModel = self.ui.process_view.model()
        column: int = self.ui.process_view.selectionModel().currentIndex().column()

        changed: bool = model.insertColumn(column + 1)
        if changed:
            model.setHeaderData(column + 1, Qt.Horizontal, "[No header]", Qt.EditRole)

        self.process_update_actions()

    @Slot()
    def on_doubleclick_library_view(self, library_index: QModelIndex) -> None:

        preselected_process_index: QModelIndex = self.ui.process_view.selectionModel().currentIndex()
        parent_of_preselected_process_index: QModelIndex = preselected_process_index.parent()
        process_model: QAbstractItemModel = self.ui.process_view.model()

        if not process_model.insertRow(preselected_process_index.row() + 1, parent_of_preselected_process_index):
            return

        self.process_update_actions()

        parent_of_library_index = library_index.parent()
        library_model: QAbstractItemModel = self.ui.library_view.model()
        library_row = library_index.row()

        for column in range(process_model.columnCount(parent_of_preselected_process_index)):
            inserted_row = preselected_process_index.row() + 1
            inserted_item_index = process_model.index(inserted_row, column, parent_of_preselected_process_index)
            library_index_for_column = library_model.index(library_row, column, parent_of_library_index)
            library_data_for_column = library_model.data(library_index_for_column, Qt.DisplayRole)
            process_model.setData(inserted_item_index, library_data_for_column, Qt.EditRole)

    @Slot()
    def on_click_process_view(self, index: QModelIndex):
        self.mapper.setRootIndex(index.parent())
        self.mapper.setCurrentIndex(index.row())
        self.update_ui(self.mapper_index())

    @Slot()
    def insert_row(self) -> None:
        index: QModelIndex = self.ui.process_view.selectionModel().currentIndex()
        model: QAbstractItemModel = self.ui.process_view.model()
        parent: QModelIndex = index.parent()

        if not model.insertRow(index.row() + 1, parent):
            return

        self.process_update_actions()

        for column in range(model.columnCount(parent)):
            child: QModelIndex = model.index(index.row() + 1, column, parent)
            model.setData(child, "[No data]", Qt.EditRole)

    @Slot()
    def remove_column(self) -> None:
        model: QAbstractItemModel = self.ui.process_view.model()
        column: int = self.ui.process_view.selectionModel().currentIndex().column()

        if model.removeColumn(column):
            self.process_update_actions()

    @Slot()
    def remove_row(self) -> None:
        index: QModelIndex = self.ui.process_view.selectionModel().currentIndex()
        model: QAbstractItemModel = self.ui.process_view.model()

        if model.removeRow(index.row(), index.parent()):
            self.process_update_actions()

    @Slot()
    def process_update_actions(self) -> None:
        selection_model = self.ui.process_view.selectionModel()

        has_selection: bool = not selection_model.selection().isEmpty()
        self.ui.remove_row_action.setEnabled(has_selection)
        self.ui.remove_column_action.setEnabled(has_selection)
        self.ui.button_remove_row.setEnabled(has_selection)
        self.ui.button_remove_column.setEnabled(has_selection)

        self.ui.library_view.setEnabled(has_selection)

        current_index = selection_model.currentIndex()

        has_current: bool = current_index.isValid()
        self.ui.insert_row_action.setEnabled(has_current)
        self.ui.insert_column_action.setEnabled(has_current)
        self.ui.button_insert_row.setEnabled(has_current)
        self.ui.button_insert_column.setEnabled(has_current)

        if has_current:
            self.ui.process_view.closePersistentEditor(current_index)
            msg = f"Position: ({current_index.row()},{current_index.column()})"
            if not current_index.parent().isValid():
                msg += " in top level"
            self.statusBar().showMessage(msg)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
