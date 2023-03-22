from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtSql import QSqlQuery
from PySide6.QtWidgets import QMainWindow


class LibraryModel(QStandardItemModel):
    def __init__(self, parent: QMainWindow, settings: dict):
        super().__init__(parent)
        self.settings = settings

        self.allow_copies = {}
        self.is_obsolete = {}
        self.text_id = {}
        self.parent_type_id = {}
        self.child_type_ids = {}
        self.order_id = {}
        self.library_name = {}
        self.process_name = {}
        self.labels = {}
        self.labels_regex = {}
        self.db_column_names = {}

        _library_list = self._get_library_from_sql()
        self._set_class_variables(_library_list)
        self._set_child_type_ids(_library_list)

        self.max_parameters_count = max([len(value) for value in self.db_column_names.values()])

        # Build a data tree
        root_id = min(self.library_name.keys())
        root_item = self.invisibleRootItem()
        self._set_data_to_item(root_item, root_id)
        self._add_children_to_item_recursively(root_item, root_id)

    def _add_children_to_item_recursively(self, parent_item: QStandardItem, parent_type_id: int) -> QStandardItem:
        """Recursive function for building tree of child_type_ids"""
        if parent_type_id not in self.child_type_ids:
            return parent_item  # if no children, return parent_item as is

        # There are children. Add children to parent_item before returning it.
        for type_id in self.child_type_ids.get(parent_type_id):
            item = QStandardItem()
            self._set_data_to_item(item, type_id)
            self._add_children_to_item_recursively(item, type_id)
            parent_item.appendRow(item)
        return parent_item

    def _set_data_to_item(self, item: QStandardItem, type_id: int):
        item.setData(self.library_name[type_id], Qt.DisplayRole)
        item.setData(type_id, Qt.UserRole + 1)
        item.setData(self.text_id[type_id], Qt.UserRole + 2)
        item.setData(self.allow_copies[type_id], Qt.UserRole + 3)
        item.setData(self.parent_type_id[type_id], Qt.UserRole + 4)
        item.setData(self.order_id[type_id], Qt.UserRole + 5)
        item.setData(self.process_name[type_id], Qt.UserRole + 6)
        item.setData(self.labels[type_id], Qt.UserRole + 7)
        item.setData(self.labels_regex[type_id], Qt.UserRole + 8)
        item.setData(self.db_column_names[type_id], Qt.UserRole + 9)

    def _get_library_from_sql(self):
        # --------------------------------------------
        # text_id VARCHAR(511) NOT NULL,
        # type_id SMALLINT PRIMARY KEY,
        # parent_type_id SMALLINT,
        # order_id BIGINT NOT NULL,
        # allow_copies BOOL NOT NULL DEFAULT FALSE,
        # library_name VARCHAR(511) NOT NULL,
        # process_name VARCHAR(511) NOT NULL,
        # labels VARCHAR(4095) DEFAULT NULL,
        # labels_regex VARCHAR(4095) DEFAULT NULL,
        # db_column_names VARCHAR(2047) DEFAULT NULL,
        # is_obsolete BOOL NOT NULL DEFAULT FALSE,

        text_id, type_id, parent_type_id, order_id, allow_copies, library_name, process_name, \
            labels, labels_regex, db_column_names, is_obsolete = range(11)

        operations_library_records = []
        query = QSqlQuery(self.settings['connection'])
        query.exec(
            f"""
            SELECT 
                text_id, type_id, parent_type_id, order_id, allow_copies, library_name, process_name,
                labels, labels_regex, db_column_names, is_obsolete
            FROM operations_library
            """)
        if query.isActive():
            query.next()
            while query.isValid():
                _parent_type_id = query.value(parent_type_id)
                _dict = {
                    'text_id': query.value(text_id),
                    'type_id': query.value(type_id),
                    'parent_type_id': _parent_type_id if isinstance(_parent_type_id, int) else 0,  # type_id=0 for root
                    'order_id': query.value(order_id),
                    'allow_copies': query.value(allow_copies),
                    'library_name': query.value(library_name),
                    'process_name': query.value(process_name),
                    'labels': query.value(labels),
                    'labels_regex': query.value(labels_regex),
                    'db_column_names': query.value(db_column_names),
                    'is_obsolete': query.value(is_obsolete),
                }
                operations_library_records.append(_dict)
                query.next()
        query.finish()
        return operations_library_records

    def _set_class_variables(self, _library_list: list[dict]):
        """Converts list to dictionary."""
        for _item in _library_list:
            _type_id: int = _item.get('type_id')
            self.allow_copies[_type_id] = _item.get('allow_copies')  # bool
            self.is_obsolete[_type_id] = _item.get('is_obsolete')  # bool
            self.parent_type_id[_type_id] = _item.get('parent_type_id')  # int
            self.text_id[_type_id] = _item.get('text_id')  # str
            self.order_id[_type_id] = _item.get('order_id')  # int
            self.library_name[_type_id] = self._select_language(_item.get('library_name'))[0]
            self.process_name[_type_id] = self._select_language(_item.get('process_name'))[0]
            self.labels[_type_id] = self._select_language(_item.get('labels'))
            self.labels_regex[_type_id] = self._select_language(_item.get('labels_regex'))
            self.db_column_names[_type_id] = (
                _item.get('db_column_names').split('|')
                if _item.get('db_column_names')
                else []
            )

    def _set_child_type_ids(self, _library_list: list[dict]):

        def sorting_generator(_list: list, _scores: list) -> list:
            """Generator for sorting list by scores"""
            for _i in range(len(_list)):
                _min_score = min(_scores)
                _min_score_index = _scores.index(_min_score)
                _next_item = _list.pop(_min_score_index)
                del _scores[_min_score_index]
                yield _next_item

        child_parent = [(_item.get('type_id'), _item.get('parent_type_id'),) for _item in _library_list]

        for child_id, parent_id in child_parent:
            child_id: int
            parent_id: int
            if parent_id not in self.child_type_ids.keys():
                self.child_type_ids[parent_id] = []
            self.child_type_ids[parent_id].append(child_id)

        # reorder child_type_ids using order_id
        for parent_id, child_type_ids in self.child_type_ids.items():
            child_type_ids: list
            _order_id: list = [self.order_id[_child] for _child in child_type_ids]
            self.child_type_ids[parent_id] = [x for x in sorting_generator(child_type_ids, _order_id)]

    def _select_language(self, _string_value: str) -> list[str]:
        _language_code = self.settings.get('language_code')
        _list_of_strings = _string_value.split('|')
        _is_correct_language = False
        _is_next_string_language_code = False
        _return_list = []
        for _i, _string in enumerate(_list_of_strings):
            if _string == 'LANGUAGE':
                _is_next_string_language_code = True
                continue
            if _is_next_string_language_code and _string == _language_code:
                _is_next_string_language_code = False
                _is_correct_language = True
                continue
            if _is_correct_language:
                _return_list.append(_string)
        return _return_list
