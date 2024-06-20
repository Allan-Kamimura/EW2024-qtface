from PySide2.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QDialog, QLabel, QLineEdit
from PySide2.QtGui import QIcon
from PySide2.QtCore import QSize
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Set window title
        self.setWindowTitle("Main Window")

        # Set window size
        self.setGeometry(100, 100, 400, 300)

        # Add layout
        layout = QVBoxLayout(self)

        # Add button to open WiFi configuration popup
        self.config_button = QPushButton("Open WiFi Configuration", self)
        self.config_button.clicked.connect(self.open_wifi_config)
        layout.addWidget(self.config_button)

    def open_wifi_config(self):
        # Create and show WiFi configuration dialog
        wifi_dialog = WiFiConfigDialog()
        wifi_dialog.exec_()

class WiFiConfigDialog(QDialog):
    def __init__(self):
        super().__init__()

        # Set window title
        self.setWindowTitle("WiFi Configuration")

        # Set window size and position in the middle of the screen
        self.setFixedSize(300, 200)
        screen_geometry = QApplication.desktop().screenGeometry()
        self.move(screen_geometry.center() - self.rect().center())

        # Add widgets
        layout = QVBoxLayout(self)

        # Label for WiFi Configuration
        wifi_label = QLabel("WiFi Configuration", self)
        layout.addWidget(wifi_label)

        # Text field for WiFi name
        self.wifi_name_edit = QLineEdit(self)
        self.wifi_name_edit.setPlaceholderText("Enter WiFi Name")
        layout.addWidget(self.wifi_name_edit)

        # Text field for WiFi password
        self.wifi_password_edit = QLineEdit(self)
        self.wifi_password_edit.setPlaceholderText("Enter WiFi Password")
        layout.addWidget(self.wifi_password_edit)

        # Add button
        button = QPushButton("Save", self)
        button.clicked.connect(self.save_config)
        layout.addWidget(button)

    def save_config(self):
        # Implement saving WiFi configuration here
        wifi_name = self.wifi_name_edit.text()
        wifi_password = self.wifi_password_edit.text()
        print("WiFi Name:", wifi_name)
        print("WiFi Password:", wifi_password)

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
