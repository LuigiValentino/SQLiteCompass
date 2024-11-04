import sqlite3
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (
    QMainWindow, QTableWidgetItem, QFileDialog, QMessageBox, QInputDialog, QPushButton,
    QVBoxLayout, QWidget, QHBoxLayout, QTextEdit, QTabWidget, QLabel, QFormLayout, QDialog
)
from PyQt5.QtGui import QIcon


class SQLiteCompass(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SQLite Compass")
        self.setWindowIcon(QIcon("./logo.webp"))
        self.setGeometry(100, 100, 1000, 700)
        self.conn = None
        self.cursor = None
        self.current_db_path = None
        self.initUI()

    def initUI(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Archivo")
        
        new_action = QtWidgets.QAction("Nueva Base de Datos", self)
        new_action.triggered.connect(self.create_database)
        file_menu.addAction(new_action)

        open_action = QtWidgets.QAction("Abrir Base de Datos", self)
        open_action.triggered.connect(self.open_database)
        file_menu.addAction(open_action)

        close_action = QtWidgets.QAction("Cerrar Base de Datos", self)
        close_action.triggered.connect(self.close_database)
        file_menu.addAction(close_action)

        main_layout = QVBoxLayout()
        tabs = QTabWidget()
        main_layout.addWidget(tabs)

        tables_tab = QWidget()
        tables_tab_layout = QHBoxLayout()

        left_panel = QVBoxLayout()
        
        self.table_list = QtWidgets.QListWidget()
        self.table_list.itemClicked.connect(self.load_table_data)
        left_panel.addWidget(self.table_list)

        self.create_table_btn = QPushButton("Crear Tabla")
        self.create_table_btn.clicked.connect(self.create_table)
        left_panel.addWidget(self.create_table_btn)

        tables_tab_layout.addLayout(left_panel, 1)

        right_panel = QVBoxLayout()

        action_layout = QHBoxLayout()
        
        self.add_record_btn = QPushButton("+ Agregar Registro")
        self.add_record_btn.clicked.connect(self.insert_record)
        action_layout.addWidget(self.add_record_btn)
        
        self.edit_record_btn = QPushButton("Editar Registro")
        self.edit_record_btn.clicked.connect(self.enable_editing)
        action_layout.addWidget(self.edit_record_btn)
        
        self.delete_record_btn = QPushButton("- Eliminar Registro")
        self.delete_record_btn.clicked.connect(self.delete_record)
        action_layout.addWidget(self.delete_record_btn)

        self.refresh_btn = QPushButton("Actualizar")
        self.refresh_btn.clicked.connect(self.refresh_table)
        action_layout.addWidget(self.refresh_btn)

        right_panel.addLayout(action_layout)

        self.data_table = QtWidgets.QTableWidget()
        self.data_table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.data_table.itemDoubleClicked.connect(self.enable_editing)
        right_panel.addWidget(self.data_table)

        tables_tab_layout.addLayout(right_panel, 3)
        tables_tab.setLayout(tables_tab_layout)
        tabs.addTab(tables_tab, "Tablas")

        sql_tab = QWidget()
        sql_tab_layout = QVBoxLayout()

        self.sql_editor = QTextEdit()
        self.sql_editor.setPlaceholderText("Escribe tu consulta SQL aquí...")
        sql_tab_layout.addWidget(self.sql_editor)

        execute_sql_btn = QPushButton("Ejecutar SQL")
        execute_sql_btn.clicked.connect(self.execute_sql)
        sql_tab_layout.addWidget(execute_sql_btn)

        self.sql_results = QTextEdit()
        self.sql_results.setReadOnly(True)
        sql_tab_layout.addWidget(self.sql_results)

        sql_tab.setLayout(sql_tab_layout)
        tabs.addTab(sql_tab, "Consulta SQL")

        self.footer = QLabel("SQLiteCompass - Programado por LuigiValentino - Estado: Sin conexión | Base de datos: Ninguna")
        main_layout.addWidget(self.footer)

        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def create_database(self):
        db_path, _ = QFileDialog.getSaveFileName(self, "Crear Nueva Base de Datos", "", "SQLite Files (*.sqlite *.db)")
        if db_path:
            self.conn = sqlite3.connect(db_path)
            self.cursor = self.conn.cursor()
            self.current_db_path = db_path
            self.update_table_list()
            self.update_footer("Base de datos creada en " + db_path)

    def open_database(self):
        db_path, _ = QFileDialog.getOpenFileName(self, "Abrir Base de Datos", "", "SQLite Files (*.sqlite *.db)")
        if db_path:
            self.conn = sqlite3.connect(db_path)
            self.cursor = self.conn.cursor()
            self.current_db_path = db_path
            self.update_table_list()
            self.update_footer("Conectado a " + db_path)

    def close_database(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            self.table_list.clear()
            self.data_table.clear()
            self.sql_results.clear()
            self.update_footer("Conexión cerrada.")

    def update_table_list(self):
        if not self.conn:
            return
        self.table_list.clear()
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = self.cursor.fetchall()
        for table in tables:
            self.table_list.addItem(table[0])

    def load_table_data(self, item):
        if not self.conn:
            return
        table_name = item.text()
        self.cursor.execute(f"SELECT * FROM {table_name}")
        rows = self.cursor.fetchall()
        columns = [description[0] for description in self.cursor.description]

        self.data_table.setColumnCount(len(columns))
        self.data_table.setRowCount(len(rows))
        self.data_table.setHorizontalHeaderLabels(columns)

        for row_idx, row_data in enumerate(rows):
            for col_idx, col_data in enumerate(row_data):
                self.data_table.setItem(row_idx, col_idx, QTableWidgetItem(str(col_data)))
        
        self.update_footer(f"Tabla '{table_name}' cargada con {len(rows)} registros.")

    def refresh_table(self):
        current_item = self.table_list.currentItem()
        if current_item:
            self.load_table_data(current_item)

    def create_table(self):
        if not self.conn:
            QMessageBox.warning(self, "SQLite Compass", "Primero abre una base de datos.")
            return

        table_name, ok = QInputDialog.getText(self, "Crear Tabla", "Nombre de la tabla:")
        if not ok or not table_name:
            return
        
        columns, ok = QInputDialog.getText(self, "Crear Tabla", "Defina columnas (formato: nombre tipo, ...):")
        if not ok or not columns:
            return

        try:
            self.cursor.execute(f"CREATE TABLE {table_name} ({columns})")
            self.conn.commit()
            self.update_table_list()
            self.update_footer(f"Tabla '{table_name}' creada exitosamente.")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "SQLite Compass", f"Error al crear tabla: {e}")

    def insert_record(self):
        if not self.conn or not self.table_list.currentItem():
            QMessageBox.warning(self, "SQLite Compass", "Primero seleccione una tabla.")
            return

        table_name = self.table_list.currentItem().text()
        columns = [self.data_table.horizontalHeaderItem(i).text() for i in range(self.data_table.columnCount())]
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Agregar Registro")
        layout = QFormLayout(dialog)
        
        fields = {}
        for column in columns:
            fields[column] = QtWidgets.QLineEdit(dialog)
            layout.addRow(column, fields[column])
        
        buttons = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(lambda: self.add_record_to_db(dialog, table_name, fields))
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(dialog.reject)
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addRow(buttons)
        
        dialog.exec_()

    def add_record_to_db(self, dialog, table_name, fields):
        values = [field.text() for field in fields.values()]
        placeholders = ", ".join("?" for _ in values)
        try:
            self.cursor.execute(f"INSERT INTO {table_name} VALUES ({placeholders})", values)
            self.conn.commit()
            dialog.accept()
            self.load_table_data(self.table_list.currentItem())
            self.update_footer(f"Registro agregado en '{table_name}'.")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "SQLite Compass", f"Error al insertar registro: {e}")

    def enable_editing(self):
        self.data_table.setEditTriggers(QtWidgets.QTableWidget.AllEditTriggers)
        self.update_footer("Modo de edición activado para los registros de la tabla.")

    def delete_record(self):
        if not self.conn or not self.table_list.currentItem():
            QMessageBox.warning(self, "SQLite Compass", "Primero seleccione una tabla.")
            return
        current_row = self.data_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "SQLite Compass", "Seleccione un registro para eliminar.")
            return

        table_name = self.table_list.currentItem().text()
        primary_key = self.data_table.horizontalHeaderItem(0).text()
        primary_key_value = self.data_table.item(current_row, 0).text()
        
        confirm = QMessageBox.question(
            self, "Eliminar Registro", f"¿Seguro que quieres eliminar el registro con {primary_key} = {primary_key_value}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            try:
                self.cursor.execute(f"DELETE FROM {table_name} WHERE {primary_key} = ?", (primary_key_value,))
                self.conn.commit()
                self.load_table_data(self.table_list.currentItem())
                self.update_footer(f"Registro eliminado de '{table_name}'.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "SQLite Compass", f"Error al eliminar registro: {e}")

    def execute_sql(self):
        if not self.conn:
            QMessageBox.warning(self, "SQLite Compass", "Primero abre una base de datos.")
            return
        query = self.sql_editor.toPlainText()
        try:
            self.cursor.execute(query)
            if query.strip().lower().startswith("select"):
                rows = self.cursor.fetchall()
                columns = [description[0] for description in self.cursor.description]
                results_text = "\t".join(columns) + "\n"
                for row in rows:
                    results_text += "\t".join(str(cell) for cell in row) + "\n"
                self.sql_results.setPlainText(results_text)
            else:
                self.conn.commit()
                self.update_footer("Consulta ejecutada exitosamente.")
                QMessageBox.information(self, "SQLite Compass", "Consulta ejecutada exitosamente.")
                self.update_table_list()
                self.refresh_table()
        except sqlite3.Error as e:
            self.sql_results.setPlainText(f"Error: {e}")
            self.update_footer("Error en la consulta.")

    def update_footer(self, text):
        self.footer.setText(f"SQLiteCompass - Programado por LuigiValentino - Estado: {text} | Base de datos: {self.current_db_path if self.current_db_path else 'Ninguna'}")

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = SQLiteCompass()
    window.show()
    sys.exit(app.exec_())
