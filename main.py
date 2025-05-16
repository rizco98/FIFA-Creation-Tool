#!/usr/bin/env python3

import sys
import os

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                                QTableWidget, QTableWidgetItem, QMessageBox,
                                QTabWidget, QComboBox, QSpinBox, QLineEdit,
                                QGroupBox, QFormLayout, QHeaderView, QScrollArea)
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont, QAction
except ImportError:
    print("Error: PyQt6 is not installed. Please install it using:")
    print("pip install PyQt6")
    sys.exit(1)

# Import squad file parser
try:
    from database.squad_parser import SquadFile
except ImportError as e:
    print(f"Error importing squad parser: {e}")
    print("Make sure you're running the script from the correct directory")
    sys.exit(1)

class FC25Editor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FC25 Database Editor")
        self.setGeometry(100, 100, 1600, 900)
        
        try:
            # Main widget and layout
            main_widget = QWidget()
            self.setCentralWidget(main_widget)
            layout = QVBoxLayout(main_widget)
            
            # Create main tab widget
            self.tabs = QTabWidget()
            
            # Add menu bar first
            self.setup_menu_bar()
            
            # Initialize squad_file as None
            self.squad_file = None
            
            layout.addWidget(self.tabs)
            
            # Set dark theme
            self.apply_dark_theme()
            
            # Store current player details
            self.current_player_details = None
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to initialize application: {str(e)}")
            raise

    def setup_menu_bar(self):
        """Setup the menu bar"""
        try:
            menubar = self.menuBar()
            
            # File menu
            file_menu = menubar.addMenu('File')
            
            # Open action
            open_action = QAction('Open Squad File...', self)
            open_action.setShortcut('Ctrl+O')
            open_action.triggered.connect(self.open_squad_file_dialog)
            file_menu.addAction(open_action)
            
            # Save action
            save_action = QAction('Save', self)
            save_action.setShortcut('Ctrl+S')
            save_action.triggered.connect(self.save_squad_file)
            file_menu.addAction(save_action)
            
            # Exit action
            exit_action = QAction('Exit', self)
            exit_action.setShortcut('Ctrl+Q')
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to setup menu bar: {str(e)}")
            raise
    
    def open_squad_file_dialog(self):
        """Open squad file dialog"""
        try:
            # Get the EA FC 25 settings directory
            settings_dir = os.path.expandvars(r"%LOCALAPPDATA%\EA SPORTS FC 25\settings")
            if not os.path.exists(settings_dir):
                QMessageBox.warning(self, "Warning", 
                    f"EA SPORTS FC 25 settings directory not found at:\n{settings_dir}\n\nPlease select the squad file manually.")
                settings_dir = ""
            
            file_name, _ = QFileDialog.getOpenFileName(
                self,
                "Open Squad File",
                settings_dir,
                "Squad Files (Squads*);;All Files (*)"
            )
            
            if file_name:
                self.load_squad_file(file_name)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file dialog: {str(e)}")
    
    def load_squad_file(self, file_path):
        """Load squad file"""
        try:
            print(f"Loading squad file from: {file_path}")
            print(f"File exists: {os.path.exists(file_path)}")
            print(f"File size: {os.path.getsize(file_path)} bytes")
            
            self.squad_file = SquadFile(file_path)
            
            if not os.path.exists(file_path):
                # If squad file doesn't exist, create it with default data
                print("Creating new squad file with default data")
                from database.countries import COUNTRIES_DATABASE
                from database.leagues import LEAGUES_DATABASE
                from database.teams import TEAMS_DATABASE
                from database.players import PLAYERS_DATABASE
                from database.stadiums import STADIUMS_DATABASE
                from database.tournaments import TOURNAMENTS_DATABASE
                from database.kits import KITS_DATABASE
                
                self.squad_file.countries = COUNTRIES_DATABASE.copy()
                self.squad_file.leagues = LEAGUES_DATABASE.copy()
                self.squad_file.teams = TEAMS_DATABASE.copy()
                self.squad_file.players = PLAYERS_DATABASE.copy()
                self.squad_file.stadiums = STADIUMS_DATABASE.copy()
                self.squad_file.tournaments = TOURNAMENTS_DATABASE.copy()
                self.squad_file.kits = KITS_DATABASE.copy()
                
                self.squad_file.save()
            else:
                print("Loading existing squad file")
                self.squad_file.load()
            
            # Refresh all tabs
            self.refresh_all_tabs()
            
            # Update window title
            self.setWindowTitle(f"FC25 Database Editor - {os.path.basename(file_path)}")
            
            QMessageBox.information(self, "Success", "Squad file loaded successfully!")
            
        except Exception as e:
            error_msg = f"Failed to load squad file: {str(e)}\nFile path: {file_path}"
            if os.path.exists(file_path):
                error_msg += f"\nFile size: {os.path.getsize(file_path)} bytes"
            QMessageBox.critical(self, "Error", error_msg)
            raise
    
    def save_squad_file(self):
        """Save squad file"""
        try:
            self.squad_file.save()
            QMessageBox.information(self, "Success", "Squad file saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save squad file: {str(e)}")
    
    def refresh_all_tabs(self):
        """Refresh all tabs with current data"""
        # Remove all tabs
        while self.tabs.count():
            self.tabs.removeTab(0)
        
        # Re-add all tabs
        self.setup_countries_tab()
        self.setup_leagues_tab()
        self.setup_teams_tab()
        self.setup_players_tab()
        self.setup_stadiums_tab()
        self.setup_tournaments_tab()
        self.setup_kits_tab()
    
    def setup_countries_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Top section with search and controls
        top_layout = QHBoxLayout()
        
        # Search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        search_edit = QLineEdit()
        search_edit.setPlaceholderText("Search countries...")
        search_edit.textChanged.connect(self.filter_countries)
        search_layout.addWidget(search_label)
        search_layout.addWidget(search_edit)
        top_layout.addLayout(search_layout)
        
        # Add spacer
        top_layout.addStretch()
        
        # Control buttons
        buttons_layout = QHBoxLayout()
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.save_country_changes)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_countries)
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(refresh_btn)
        top_layout.addLayout(buttons_layout)
        
        layout.addLayout(top_layout)
        
        # Split view
        split_layout = QHBoxLayout()
        
        # Countries table
        table_group = QGroupBox("Countries List")
        table_layout = QVBoxLayout()
        self.countries_table = QTableWidget()
        self.countries_table.setColumnCount(4)
        self.countries_table.setHorizontalHeaderLabels(["ID", "Name", "Confederation", "Rating"])
        
        # Set column widths
        header = self.countries_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        # Add data from squad file
        for country_id, data in self.squad_file.get_countries().items():
            row = self.countries_table.rowCount()
            self.countries_table.insertRow(row)
            self.countries_table.setItem(row, 0, QTableWidgetItem(country_id))
            self.countries_table.setItem(row, 1, QTableWidgetItem(data[0]))  # Name
            self.countries_table.setItem(row, 2, QTableWidgetItem(data[3]))  # Confederation
            self.countries_table.setItem(row, 3, QTableWidgetItem(data[6]))  # Rating
        
        self.countries_table.currentItemChanged.connect(self.show_country_details)
        table_layout.addWidget(self.countries_table)
        table_group.setLayout(table_layout)
        split_layout.addWidget(table_group, stretch=1)
        
        # Country details panel
        details_group = QGroupBox("Country Details")
        details_layout = QVBoxLayout()
        
        # Create a scroll area for details
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        details_widget = QWidget()
        self.country_form = QFormLayout(details_widget)
        
        # Basic Information
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout()
        
        self.country_id_edit = QLineEdit()
        self.country_id_edit.setReadOnly(True)
        basic_layout.addRow("ID:", self.country_id_edit)
        
        self.country_name_edit = QLineEdit()
        basic_layout.addRow("Full Name:", self.country_name_edit)
        
        self.country_short_name_edit = QLineEdit()
        basic_layout.addRow("Short Name:", self.country_short_name_edit)
        
        self.country_abbrev_edit = QLineEdit()
        basic_layout.addRow("Abbreviation:", self.country_abbrev_edit)
        
        self.country_iso_edit = QLineEdit()
        basic_layout.addRow("ISO Code:", self.country_iso_edit)
        
        basic_group.setLayout(basic_layout)
        self.country_form.addRow(basic_group)
        
        # Confederation and Ratings
        ratings_group = QGroupBox("Confederation and Ratings")
        ratings_layout = QFormLayout()
        
        self.confederation_combo = QComboBox()
        self.confederation_combo.addItems(["UEFA", "CONMEBOL", "CONCACAF", "CAF", "AFC", "OFC"])
        ratings_layout.addRow("Confederation:", self.confederation_combo)
        
        self.country_level_spin = QSpinBox()
        self.country_level_spin.setRange(1, 5)
        ratings_layout.addRow("Level:", self.country_level_spin)
        
        self.national_rating_spin = QSpinBox()
        self.national_rating_spin.setRange(1, 99)
        ratings_layout.addRow("National Team Rating:", self.national_rating_spin)
        
        self.flag_code_edit = QLineEdit()
        ratings_layout.addRow("Flag Code:", self.flag_code_edit)
        
        ratings_group.setLayout(ratings_layout)
        self.country_form.addRow(ratings_group)
        
        scroll.setWidget(details_widget)
        details_layout.addWidget(scroll)
        details_group.setLayout(details_layout)
        split_layout.addWidget(details_group, stretch=1)
        
        layout.addLayout(split_layout)
        self.tabs.addTab(tab, "Countries")
    
    def filter_countries(self, text):
        for row in range(self.countries_table.rowCount()):
            should_show = False
            for col in range(self.countries_table.columnCount()):
                item = self.countries_table.item(row, col)
                if item and text.lower() in item.text().lower():
                    should_show = True
                    break
            self.countries_table.setRowHidden(row, not should_show)
    
    def show_country_details(self, current, previous):
        if not current:
            return
            
        row = current.row()
        country_id = self.countries_table.item(row, 0).text()
        country_data = self.squad_file.get_countries().get(country_id)
        
        if country_data:
            self.country_id_edit.setText(country_id)
            self.country_name_edit.setText(country_data[0])
            self.country_short_name_edit.setText(country_data[1])
            self.country_abbrev_edit.setText(country_data[2])
            self.confederation_combo.setCurrentText(country_data[3])
            self.country_iso_edit.setText(country_data[4])
            self.country_level_spin.setValue(int(country_data[5]))
            self.national_rating_spin.setValue(int(country_data[6]))
            self.flag_code_edit.setText(country_data[7])
    
    def save_country_changes(self):
        current_row = self.countries_table.currentRow()
        if current_row < 0:
            return
            
        country_id = self.country_id_edit.text()
        new_data = [
            self.country_name_edit.text(),
            self.country_short_name_edit.text(),
            self.country_abbrev_edit.text(),
            self.confederation_combo.currentText(),
            self.country_iso_edit.text(),
            str(self.country_level_spin.value()),
            str(self.national_rating_spin.value()),
            self.flag_code_edit.text()
        ]
        
        # Update squad file
        self.squad_file.update_country(country_id, new_data)
        
        # Update table
        self.countries_table.setItem(current_row, 1, QTableWidgetItem(new_data[0]))
        self.countries_table.setItem(current_row, 2, QTableWidgetItem(new_data[3]))
        self.countries_table.setItem(current_row, 3, QTableWidgetItem(new_data[6]))
        
        QMessageBox.information(self, "Success", "Country data saved successfully!")
    
    def refresh_countries(self):
        current_row = self.countries_table.currentRow()
        if current_row >= 0:
            self.show_country_details(self.countries_table.item(current_row, 0), None)
    
    def setup_leagues_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_edit = QLineEdit()
        search_edit.setPlaceholderText("Search leagues...")
        search_layout.addWidget(search_edit)
        layout.addLayout(search_layout)
        
        # Leagues table
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["ID", "Name", "Country", "Division", "Teams"])
        
        # Add data
        for league_id, data in self.squad_file.get_leagues().items():
            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(league_id))
            for col, value in enumerate(data[:4], 1):
                table.setItem(row, col, QTableWidgetItem(str(value)))
        
        layout.addWidget(table)
        self.tabs.addTab(tab, "Leagues")
    
    def setup_teams_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_edit = QLineEdit()
        search_edit.setPlaceholderText("Search teams...")
        search_layout.addWidget(search_edit)
        layout.addLayout(search_layout)
        
        # Teams table
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels(["ID", "Name", "League", "OVR", "ATT", "MID", "DEF"])
        
        # Add data
        for team_id, data in self.squad_file.get_teams().items():
            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(team_id))
            for col, value in enumerate(data[:6], 1):
                table.setItem(row, col, QTableWidgetItem(str(value)))
        
        layout.addWidget(table)
        self.tabs.addTab(tab, "Teams")
    
    def setup_players_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_edit = QLineEdit()
        search_edit.setPlaceholderText("Search players...")
        search_edit.textChanged.connect(self.filter_players)
        search_layout.addWidget(search_edit)
        layout.addLayout(search_layout)
        
        # Split view
        split_layout = QHBoxLayout()
        
        # Players table
        table_group = QGroupBox("Players")
        table_layout = QVBoxLayout()
        self.players_table = QTableWidget()
        self.players_table.setColumnCount(11)
        self.players_table.setHorizontalHeaderLabels([
            "ID", "Name", "OVR", "POS", "Age", "Team", "League", "NAT", "Height", "Weight", "Foot"
        ])
        
        # Set column widths
        header = self.players_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(10, QHeaderView.ResizeMode.ResizeToContents)
        
        # Add data
        for player_id, data in self.squad_file.get_players().items():
            row = self.players_table.rowCount()
            self.players_table.insertRow(row)
            self.players_table.setItem(row, 0, QTableWidgetItem(player_id))
            for col, value in enumerate(data[:10], 1):
                if isinstance(value, dict):
                    continue
                self.players_table.setItem(row, col, QTableWidgetItem(str(value)))
        
        self.players_table.currentItemChanged.connect(self.show_player_details)
        table_layout.addWidget(self.players_table)
        table_group.setLayout(table_layout)
        split_layout.addWidget(table_group, stretch=2)
        
        # Player details panel
        details_group = QGroupBox("Player Details")
        details_layout = QVBoxLayout()
        
        # Create a scroll area for details
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        details_widget = QWidget()
        self.details_form = QFormLayout(details_widget)
        
        # Basic Info
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout()
        self.name_label = QLabel()
        basic_layout.addRow("Name:", self.name_label)
        self.ovr_label = QLabel()
        basic_layout.addRow("Overall:", self.ovr_label)
        self.pos_label = QLabel()
        basic_layout.addRow("Position:", self.pos_label)
        self.team_label = QLabel()
        basic_layout.addRow("Team:", self.team_label)
        self.league_label = QLabel()
        basic_layout.addRow("League:", self.league_label)
        self.nation_label = QLabel()
        basic_layout.addRow("Nationality:", self.nation_label)
        basic_group.setLayout(basic_layout)
        self.details_form.addRow(basic_group)
        
        # Physical
        physical_group = QGroupBox("Physical")
        physical_layout = QFormLayout()
        self.height_label = QLabel()
        physical_layout.addRow("Height:", self.height_label)
        self.weight_label = QLabel()
        physical_layout.addRow("Weight:", self.weight_label)
        self.foot_label = QLabel()
        physical_layout.addRow("Preferred Foot:", self.foot_label)
        physical_group.setLayout(physical_layout)
        self.details_form.addRow(physical_group)
        
        # Attack Stats
        attack_group = QGroupBox("Attack Stats")
        self.attack_layout = QFormLayout()
        attack_group.setLayout(self.attack_layout)
        self.details_form.addRow(attack_group)
        
        # Midfield Stats
        midfield_group = QGroupBox("Midfield Stats")
        self.midfield_layout = QFormLayout()
        midfield_group.setLayout(self.midfield_layout)
        self.details_form.addRow(midfield_group)
        
        # Defense Stats
        defense_group = QGroupBox("Defense Stats")
        self.defense_layout = QFormLayout()
        defense_group.setLayout(self.defense_layout)
        self.details_form.addRow(defense_group)
        
        # GK Stats
        gk_group = QGroupBox("Goalkeeper Stats")
        self.gk_layout = QFormLayout()
        gk_group.setLayout(self.gk_layout)
        self.details_form.addRow(gk_group)
        
        scroll.setWidget(details_widget)
        details_layout.addWidget(scroll)
        details_group.setLayout(details_layout)
        split_layout.addWidget(details_group, stretch=1)
        
        layout.addLayout(split_layout)
        self.tabs.addTab(tab, "Players")
    
    def show_player_details(self, current, previous):
        if not current:
            return
            
        row = current.row()
        player_id = self.players_table.item(row, 0).text()
        player_data = self.squad_file.get_players().get(player_id)
        
        # Update basic info
        self.name_label.setText(player_data[0])
        self.ovr_label.setText(player_data[1])
        self.pos_label.setText(player_data[2])
        self.team_label.setText(player_data[4])
        self.league_label.setText(player_data[9])
        self.nation_label.setText(player_data[5])
        self.height_label.setText(f"{player_data[6]} cm")
        self.weight_label.setText(f"{player_data[7]} kg")
        self.foot_label.setText(player_data[8])
        
        # Clear previous stats
        self.clear_layout(self.attack_layout)
        self.clear_layout(self.midfield_layout)
        self.clear_layout(self.defense_layout)
        self.clear_layout(self.gk_layout)
        
        # Update stats
        attack_stats = player_data[10]
        for stat, value in attack_stats.items():
            self.attack_layout.addRow(f"{stat}:", QLabel(value))
            
        midfield_stats = player_data[11]
        for stat, value in midfield_stats.items():
            self.midfield_layout.addRow(f"{stat}:", QLabel(value))
            
        defense_stats = player_data[12]
        for stat, value in defense_stats.items():
            self.defense_layout.addRow(f"{stat}:", QLabel(value))
            
        gk_stats = player_data[13]
        for stat, value in gk_stats.items():
            self.gk_layout.addRow(f"{stat}:", QLabel(value))
    
    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def filter_players(self, text):
        for row in range(self.players_table.rowCount()):
            show = False
            for col in range(1, 8):  # Search in name, team, league, nationality
                item = self.players_table.item(row, col)
                if item and text.lower() in item.text().lower():
                    show = True
                    break
            self.players_table.setRowHidden(row, not show)
    
    def setup_stadiums_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_edit = QLineEdit()
        search_edit.setPlaceholderText("Search stadiums...")
        search_layout.addWidget(search_edit)
        layout.addLayout(search_layout)
        
        # Stadiums table
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            "ID", "Name", "City", "Country", "Capacity", "Team", "Built"
        ])
        
        # Add data
        for stadium_id, data in self.squad_file.get_stadiums().items():
            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(stadium_id))
            for col, value in enumerate(data[:6], 1):
                table.setItem(row, col, QTableWidgetItem(str(value)))
        
        layout.addWidget(table)
        self.tabs.addTab(tab, "Stadiums")
    
    def setup_tournaments_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_edit = QLineEdit()
        search_edit.setPlaceholderText("Search tournaments...")
        search_layout.addWidget(search_edit)
        layout.addLayout(search_layout)
        
        # Tournaments table
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            "ID", "Name", "Type", "Region", "Teams", "Prize", "Champion"
        ])
        
        # Add data
        for tournament_id, data in self.squad_file.get_tournaments().items():
            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(tournament_id))
            for col, value in enumerate(data, 1):
                table.setItem(row, col, QTableWidgetItem(str(value)))
        
        layout.addWidget(table)
        self.tabs.addTab(tab, "Tournaments")
    
    def setup_kits_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_edit = QLineEdit()
        search_edit.setPlaceholderText("Search kits...")
        search_layout.addWidget(search_edit)
        layout.addLayout(search_layout)
        
        # Kits table
        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            "ID", "Team", "Season", "Type", "Color 1", "Color 2", "Brand", "Sponsor"
        ])
        
        # Add data
        for kit_id, data in self.squad_file.get_kits().items():
            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(kit_id))
            for col, value in enumerate(data, 1):
                table.setItem(row, col, QTableWidgetItem(str(value)))
        
        layout.addWidget(table)
        self.tabs.addTab(tab, "Kits")
    
    def apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #353535;
                color: #ffffff;
                padding: 8px 20px;
                border: 1px solid #555555;
            }
            QTabBar::tab:selected {
                background-color: #454545;
            }
            QTableWidget {
                background-color: #333333;
                color: #ffffff;
                gridline-color: #555555;
            }
            QHeaderView::section {
                background-color: #404040;
                color: #ffffff;
                padding: 4px;
                border: 1px solid #555555;
            }
            QLineEdit {
                background-color: #333333;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 2px;
                padding: 4px;
            }
            QPushButton {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 2px;
                padding: 5px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #303030;
            }
            QGroupBox {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
                margin-top: 0.5em;
                padding-top: 0.5em;
            }
            QGroupBox::title {
                color: #ffffff;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
            QLabel {
                color: #ffffff;
            }
            QScrollArea {
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: #2b2b2b;
                width: 10px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #555555;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        window = FC25Editor()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)