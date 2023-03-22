import os
import sys

from PySide6.QtSql import QSqlDatabase
from PySide6.QtWidgets import \
    QApplication, QErrorMessage, QStatusBar, QMainWindow
from PySide6.QtCore import \
    Qt, QCoreApplication, QModelIndex, Slot, QItemSelectionModel, QAbstractProxyModel
from PySide6.QtGui import \
    QIcon, QPixmap, QGuiApplication
from PySide6.QtWidgets import \
    QSizePolicy, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QSpacerItem, QTreeView, QGroupBox, QAbstractItemView, \
    QFormLayout, QLineEdit, QLabel, QDataWidgetMapper

from ProcessEditor.library_model import LibraryModel
from ProcessEditor.process_model import ProcessModel


def run() -> None:
    """Start main window"""
    app = QApplication(sys.argv)
    connection = set_database_connection()
    w = Main(connection)
    w.show()
    sys.exit(app.exec())


def set_database_connection() -> [QSqlDatabase, None]:
    """
    Make connection to the database. Returns status of connection.
    If connection is well established database is accessible
    using 'connection = QSqlDatabase.database('ForgelabDB', open=False)'.
    """
    host = "localhost"
    postgres_user = "postgres"
    password = "2008"
    database = "forgelab_2"
    connection = QSqlDatabase.addDatabase('QPSQL')  # , 'ForgelabDB')
    if connection.isValid():
        connection.setHostName(host)
        connection.setDatabaseName(database)
        connection.setUserName(postgres_user)
        connection.setPassword(password)
        connection.setPort(5432)
        status = connection.open()
        if status:
            return connection
    return None


class MainUi:
    """Class Ui defines GUI elements and their behavior"""

    def __init__(self, main_window, max_parameters_count: int):
        """Sets up GUI elements and their behavior"""
        main_window.setObjectName("EditorListWidget")
        screen = QGuiApplication.primaryScreen()
        screen_geom = screen.geometry()
        height = screen_geom.height()
        width = screen_geom.width()
        main_window.setGeometry(int(width * 0.1), int(height * 0.1), int(width * 0.8), int(height * 0.8))

        # -----------------------------------------------------------
        # LEFT LAYOUT: LIBRARY OF OPERATION TYPES (TREE VIEW)
        # -----------------------------------------------------------

        self.library_view = QTreeView(main_window)

        library_layout = QVBoxLayout()
        library_layout.addWidget(self.library_view)

        self.library_group_box = QGroupBox('', main_window)
        self.library_group_box.setLayout(library_layout)

        # ---------------------------------------------
        # MIDDLE LAYOUT: PROCESS EDITOR (TREE VIEW)
        # ---------------------------------------------

        self.button_new_process = QPushButton(main_window)
        self.button_insert_row = QPushButton(main_window)
        self.button_insert_column = QPushButton(main_window)
        self.button_remove_row = QPushButton(main_window)
        self.button_remove_column = QPushButton(main_window)
        self.button_insert_child = QPushButton(main_window)
        self.button_change_type = QPushButton(main_window)

        process_editor_buttons_layout = QHBoxLayout()
        process_editor_buttons_layout.addWidget(self.button_new_process)
        process_editor_buttons_layout.addWidget(self.button_insert_row)
        process_editor_buttons_layout.addWidget(self.button_insert_column)
        process_editor_buttons_layout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        process_editor_buttons_layout.addWidget(self.button_remove_row)
        process_editor_buttons_layout.addWidget(self.button_remove_column)
        process_editor_buttons_layout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        process_editor_buttons_layout.addWidget(self.button_insert_child)
        process_editor_buttons_layout.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        process_editor_buttons_layout.addWidget(self.button_change_type)

        self.process_editor_view = QTreeView()
        # self.view.setAlternatingRowColors(True)
        self.process_editor_view.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.process_editor_view.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.process_editor_view.setAnimated(False)
        self.process_editor_view.setAllColumnsShowFocus(True)

        process_editor_main_layout = QVBoxLayout()
        process_editor_main_layout.addLayout(process_editor_buttons_layout)
        process_editor_main_layout.addWidget(self.process_editor_view)

        self.process_editor_group_box = QGroupBox('', main_window)
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
        for i in range(max_parameters_count):
            self.line_edit_parameters.append(QLineEdit(main_window))
            self.label_parameters.append(QLabel(f'Parameter {i}', main_window))
            parameters_form_layout.addRow(self.label_parameters[i], self.line_edit_parameters[i])

        self.editor_info_view = QWidget(main_window)

        parameters_main_layout = QVBoxLayout()
        parameters_main_layout.addLayout(parameters_buttons_layout)
        parameters_main_layout.addLayout(parameters_form_layout)
        parameters_main_layout.addSpacerItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        parameters_main_layout.addWidget(self.editor_info_view)

        self.parameters_group_box = QGroupBox('Parameters', main_window)
        self.parameters_group_box.setLayout(parameters_main_layout)

        # ----------------------------------------------------------
        # MAIN LAYOUT
        # ----------------------------------------------------------

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.library_group_box, 3)
        main_layout.addWidget(self.process_editor_group_box, 4)
        main_layout.addWidget(self.parameters_group_box, 2)

        central_widget = QWidget(main_window)
        central_widget.setParent(main_window)
        central_widget.setLayout(main_layout)
        main_window.setCentralWidget(central_widget)

        self.retranslate_ui()
        self.set_icons()

    def retranslate_ui(self):
        """Sets up GUI elements and their behavior"""
        _translate = QCoreApplication.translate
        self.button_new_process.setText(_translate("EditorListWidget", "New process"))
        self.button_insert_row.setText(_translate("EditorListWidget", "Insert row"))
        self.button_insert_column.setText(_translate("EditorListWidget", "Insert column"))
        self.button_remove_row.setText(_translate("EditorListWidget", "Remove row"))
        self.button_remove_column.setText(_translate("EditorListWidget", "Remove column"))
        self.button_insert_child.setText(_translate("EditorListWidget", "Insert child"))
        self.button_change_type.setText(_translate("EditorListWidget", "Change type"))

        self.parameters_group_box.setTitle(_translate("EditorListWidget", 'Parameters of Operation'))
        self.library_group_box.setTitle(_translate("EditorListWidget", 'Library of Operations'))
        self.process_editor_group_box.setTitle(_translate("EditorListWidget", 'Process Editor'))

    def set_icons(self):
        """Sets up icons for buttons"""
        icon_dir = os.path.join(os.path.dirname(__file__), 'icons')

        self.button_new_process.setIcon(QIcon(QPixmap(os.path.join(icon_dir, "new_process.png"))))
        self.button_insert_row.setIcon(QIcon(QPixmap(os.path.join(icon_dir, "insert_above.png"))))
        self.button_change_type.setIcon(QIcon(QPixmap(os.path.join(icon_dir, "change_type.png"))))
        self.button_remove_row.setIcon(QIcon(QPixmap(os.path.join(icon_dir, "delete_row.png"))))


class Main(QMainWindow):
    """This class opens new window for editing a table of forging operations"""

    def __init__(self, connection: QSqlDatabase):
        super().__init__()
        if connection is None:
            QErrorMessage(self).showMessage("Database connection failed")
            return

        self.settings = {
            'user_id': 1,
            'process_version_id': 1,
            'language_code': 'EN',
            'connection': connection,
        }

        library_model = LibraryModel(self, self.settings)
        process_model = ProcessModel(self, self.settings)

        self.ui = MainUi(self, library_model.max_parameters_count)

        self.ui.library_view.setModel(library_model)
        self.ui.library_view.expandAll()
        for column in range(library_model.columnCount()):
            self.ui.library_view.resizeColumnToContents(column)

        self.ui.process_editor_view.setModel(process_model)
        self.ui.process_editor_view.expandAll()
        # self.ui.process_editor_view.setModel(self.settings['process_editor_models'][process_version_id])
        # for column in range(self.ui.process_editor_view.model().columnCount()):
        #     self.ui.process_editor_view.resizeColumnToContents(column)
        #     if column >= 1:
        #         self.ui.process_editor_view.hideColumn(column)
        # self.ui.process_editor_view.expandAll()

        # Mapper
        self.mapper = QDataWidgetMapper()
        self.mapper.setModel(self.ui.process_editor_view.model())
        for i in range(len(self.ui.line_edit_parameters)):
            # item with index = 0 stores name of operation, next items store values of parameters
            item_index_of_process_editor_model = i + 1
            self.mapper.addMapping(self.ui.line_edit_parameters[i], item_index_of_process_editor_model)
        self.mapper.toFirst()

        # Signals
        selection_model = self.ui.process_editor_view.selectionModel()
        selection_model.selectionChanged.connect(self.update_buttons)
        self.ui.process_editor_view.clicked.connect(self.on_click_process_editor_view)

        # Update UI
        self.ui.process_editor_view.setCurrentIndex(self.mapper_index())
        self.update_parameter_line_edits(self.mapper_index())
        self.update_buttons()

        # Process Editor Buttons
        self.ui.button_new_process.clicked.connect(self.on_click_new_process)
        self.ui.button_insert_row.clicked.connect(self.insert_row)
        self.ui.button_insert_column.clicked.connect(self.insert_column)
        self.ui.button_remove_row.clicked.connect(self.remove_row)
        self.ui.button_remove_column.clicked.connect(self.remove_column)
        self.ui.button_insert_child.clicked.connect(self.insert_child)

        # Parameters Buttons
        self.ui.button_previous.clicked.connect(self.on_click_previous)
        self.ui.button_next.clicked.connect(self.on_click_next)

        # Library View
        self.ui.library_view.doubleClicked.connect(self.on_doubleclick_library_view)

        self.update_parameter_line_edits()
        self.update_buttons()

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
            self.select_row_in_process_editor_view()
            self.update_parameter_line_edits(self.mapper_index())
            return

        self.mapper.toPrevious()
        while self.has_children(self.mapper_index()):
            # move inside the branch
            self.mapper.setRootIndex(self.mapper_index())
            self.mapper.toLast()
        self.select_row_in_process_editor_view()
        self.update_parameter_line_edits(self.mapper_index())

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
                self.select_row_in_process_editor_view()
                self.update_parameter_line_edits(self.mapper_index())
                return

            if self.mapper_row() < self.row_count(self.mapper_index()) - 1:
                # move to next row (of current branch)
                self.mapper.toNext()
                self.select_row_in_process_editor_view()
                self.update_parameter_line_edits(self.mapper_index())
                return

            # move outside the branch
            parent_index: QModelIndex = self.mapper_index().parent()
            self.mapper.setRootIndex(parent_index.parent())
            self.mapper.setCurrentIndex(parent_index.row())
            is_allow_go_inside_branch = False

    @Slot()
    def on_doubleclick_library_view(self, library_index: QModelIndex) -> None:
        """
        Receives the index of an item in self.ui.library_view.
        Reads library item's parent_type_id as library_parent_type_id.
        Then reads type_id of the parent of selected index in self.ui.process_editor_view as process_editor_parent_type_id.
        If library_parent_type_id != process_editor_parent_type_id, the inserts all missing parent items into
        the process_editor view using recursive function.
        Then inserts the item itself into the process editor view.

        Use following designations of properties in library_item:
            library_name = Qt.DisplayRole
            type_id = Qt.UserRole + 1
            text_id = Qt.UserRole + 2
            allow_copies = Qt.UserRole + 3
            parent_type_id = Qt.UserRole + 4
            order_id = Qt.UserRole + 5
            process_name = Qt.UserRole + 6
            labels = Qt.UserRole + 7
            labels_regex = Qt.UserRole + 8
            db_column_names = Qt.UserRole + 9
        """

        library_item = self.ui.library_view.model().itemFromIndex(library_index)
        library_parent_type_id = library_item.data(Qt.UserRole + 4)

        process_editor_index: QModelIndex = self.ui.process_editor_view.selectionModel().currentIndex()
        process_editor_parent_type_id = process_editor_index.parent().data(Qt.UserRole + 1)

        process_editor_index: QModelIndex = self.ui.process_editor_view.selectionModel().currentIndex()
        parent_of_process_editor_index: QModelIndex = process_editor_index.parent()

        labels = library_item.data(Qt.UserRole + 7)
        process_name = library_item.data(Qt.UserRole + 6)
        db_column_names = library_item.data(Qt.UserRole + 9)

        process_editor_model: QAbstractProxyModel = self.ui.process_editor_view.model()

        if not process_editor_model.insertRow(process_editor_index.row() + 1, parent_of_process_editor_index):
            return
        new_row = process_editor_index.row() + 1

        self.update_buttons()

        parent_of_library_index = library_index.parent()
        library_row = library_index.row()
        # get item of library_model by index

        number_of_columns = len(db_column_names)
        index_of_column_0 = process_editor_model.index(new_row, 0, parent_of_process_editor_index)
        process_editor_model.setData(index_of_column_0, process_name, Qt.EditRole)

        for i in range(number_of_columns):
            column = i + 1
            index = process_editor_model.index(new_row, column, parent_of_process_editor_index)
            process_editor_model.setData(index, labels[i], Qt.EditRole)

    @Slot()
    def on_click_process_editor_view(self, index: QModelIndex):
        self.mapper.setRootIndex(index.parent())
        self.mapper.setCurrentIndex(index.row())
        self.update_parameter_line_edits(self.mapper_index())

    def select_row_in_process_editor_view(self):
        row = self.mapper.currentIndex()
        row_index = self.ui.process_editor_view.model().index(row, 0, self.mapper.rootIndex())
        self.ui.process_editor_view.setCurrentIndex(row_index)

    def mapper_index(self):
        row = self.mapper.currentIndex()
        return self.ui.process_editor_view.model().index(row, 0, self.mapper.rootIndex())

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
        return index.row() == self.ui.process_editor_view.model().get_item(index.parent()).child_count() - 1

    @staticmethod
    def has_children(index: QModelIndex) -> bool:
        model = index.model()
        return model.hasChildren(index)

    def update_parameter_line_edits(self, index: QModelIndex = None):
        def is_last_item_of_tree(_index: QModelIndex, is_first_iteration: bool = True) -> bool:
            _model: QAbstractProxyModel = self.ui.process_editor_view.model()
            if self.is_root(_index):
                return True
            if is_first_iteration and self.has_children(_index):
                return False
            print(f"row = {index.row()}, row count = {_model.rowCount(_index.parent())}")
            if index.row() < _model.rowCount(_index.parent()) - 1:
                return False
            return is_last_item_of_tree(_index.parent(), is_first_iteration=False)

        def is_first_item_of_tree(_index: QModelIndex) -> bool:
            if _index.row() == 0 and self.is_root(_index.parent()):
                return True
            return False

        is_index = index is not None and index.isValid()
        is_model = self.ui.process_editor_view.model() is not None

        self.ui.button_previous.setEnabled(is_index and is_model and not is_first_item_of_tree(index))
        self.ui.button_next.setEnabled(is_index and is_model and not is_last_item_of_tree(index))

        max_param_count = len(self.ui.line_edit_parameters)

        is_model_empty = not is_model

        if is_model_empty:
            param_count = 0
        else:
            # item = self.ui.process_editor_view.model().item.get_item(index)
            # param_count = -1 + len(item.item_data)
            param_count = 1

        for column in range(max_param_count):
            if column >= param_count:
                self.ui.line_edit_parameters[column].hide()
                self.ui.label_parameters[column].hide()
            else:
                self.ui.line_edit_parameters[column].show()
                self.ui.label_parameters[column].show()

    @Slot()
    def insert_child(self) -> None:
        selection_model = self.ui.process_editor_view.selectionModel()
        index: QModelIndex = selection_model.currentIndex()
        model: QAbstractProxyModel = self.ui.process_editor_view.model()

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
        self.update_buttons()

    @Slot()
    def insert_column(self) -> None:
        model: QAbstractProxyModel = self.ui.process_editor_view.model()
        column: int = self.ui.process_editor_view.selectionModel().currentIndex().column()

        changed: bool = model.insertColumn(column + 1)
        if changed:
            model.setHeaderData(column + 1, Qt.Horizontal, "[No header]", Qt.EditRole)

        self.update_buttons()

    @Slot()
    def on_click_new_process(self) -> None:
        model: QAbstractProxyModel = self.ui.process_editor_view.model()
        parent = model._root_item

        status = model.insertRow(1, parent)

        if not status:
            return

        self.update_buttons()

        for column in range(model.columnCount(parent)):
            child: QModelIndex = model.index(1, column, parent)
            model.setData(child, "[No data]", Qt.EditRole)

    @Slot()
    def insert_row(self) -> None:
        index: QModelIndex = self.ui.process_editor_view.selectionModel().currentIndex()
        model: QAbstractProxyModel = self.ui.process_editor_view.model()
        parent: QModelIndex = index.parent()

        if not model.insertRow(index.row() + 1, parent):
            return

        self.update_buttons()

        for column in range(model.columnCount(parent)):
            child: QModelIndex = model.index(index.row() + 1, column, parent)
            model.setData(child, "[No data]", Qt.EditRole)

    @Slot()
    def remove_column(self) -> None:
        model: QAbstractProxyModel = self.ui.process_editor_view.model()
        column: int = self.ui.process_editor_view.selectionModel().currentIndex().column()

        if model.removeColumn(column):
            self.update_buttons()

    @Slot()
    def remove_row(self) -> None:
        index: QModelIndex = self.ui.process_editor_view.selectionModel().currentIndex()
        model: QAbstractProxyModel = self.ui.process_editor_view.model()

        if model.removeRow(index.row(), index.parent()):
            self.update_buttons()

    @Slot()
    def update_buttons(self) -> None:
        if self.ui.process_editor_view.model() is not None:
            is_empty = True if (
                    self.ui.process_editor_view.model().rowCount(self.ui.process_editor_view.model()._root_item) == 0
            ) else False
            selection_model = self.ui.process_editor_view.selectionModel()
            has_selection: bool = not selection_model.selection().isEmpty()
            current_index = selection_model.currentIndex()
            has_current: bool = current_index.isValid()
        else:
            is_empty = False
            has_selection = False
            current_index = None
            has_current = False

        self.ui.library_view.setEnabled(has_selection)
        self.ui.button_new_process.setEnabled(is_empty)
        self.ui.button_remove_row.setEnabled(has_selection)
        self.ui.button_remove_column.setEnabled(has_selection)
        self.ui.button_insert_child.setEnabled(has_selection)
        self.ui.button_change_type.setEnabled(has_selection)
        self.ui.button_insert_row.setEnabled(has_current)
        self.ui.button_insert_column.setEnabled(has_current)

        if has_current:
            self.ui.process_editor_view.closePersistentEditor(current_index)

    def on_click_library_view(self, index: QModelIndex):
        item = self.library_view.model().itemFromIndex(index)
        if not item:
            return None
        library_type_id = item.data(Qt.UserRole + 1)
        operation_id = self.selected_operation_id()
        if library_type_id is None and operation_id is None:
            return
        self.update_operation_order(operation_id, library_type_id)

    def get_indices_of_new_and_source_rows(self, position: str) -> tuple[(int, None), (int, None)]:
        """
        Takes strings 'above' and 'below'. Finds selected rows.
        Returns tuple of indices: (selected row, row above or below).
        """
        row_indices = self.selected_row_indices()
        if not row_indices:
            return None, None
        if position == "above" and min(row_indices) == 0:
            return None, None
        if position == "above":  # add above
            min_index = min(row_indices)
            new_row_index = min_index
            source_row_index = min_index
        else:  # add below
            max_index = max(row_indices)
            new_row_index = max_index + 1
            source_row_index = max_index
        return new_row_index, source_row_index

    def selected_row_indices(self) -> list:
        widgets = self.ui.process_editor_view.selectedItems()
        if widgets is None:
            return []
        return list({self.ui.process_editor_view.row(widget) for widget in widgets})
