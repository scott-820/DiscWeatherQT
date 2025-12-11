import sys, json, requests
from time import sleep
from random import randint
from dateutil import parser
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QSpinBox, QFrame,
    QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QSizePolicy,
    QLabel, QRadioButton, QButtonGroup, QComboBox, QCheckBox)
from PyQt5.QtGui import QPalette, QColor, QPixmap, QFont
from PyQt5.QtCore import Qt

import dwConfig, myStyles


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):       
        self.fig, self.axes = plt.subplots(4,1,figsize=(width, height), sharex=True, dpi=dpi, layout='constrained')
        #self.fig.constrained_layout(True)
        super().__init__(self.fig)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DiscWeather QT")
        self.setGeometry(50, 50, 1900, 1200)

        # Need a favorites dictionary - 'courseName': (lat,lon)
        self.favesExist = False
        self.faves = {}
        # Need a flag to store if current custom address was valid or not
        self.customAddressValid = False
        # Need a place to hold working courseName and Lat / Lon values
        self.courseName = 'No Entry'
        self.lat = None
        self.lon = None

        # Need a place to hold working forecast json and processed data
        self.jsonResponse = None
        # For testing, use a saved json file as the data source
        #with open("NWSForecast.json", "r") as f:

        # Need places to store last used coursename, lat, lon, jsonResponse for Favorites and Custom Address modes
        self.courseNameF = 'No Entry'
        self.latF = None
        self.lonF = None
        self.jsonResponseF = None
        self.courseNameC = 'No Entry'
        self.latC = None
        self.lonC = None
        self.jsonResponseC = None
                
        self.NUMHRS = 144       # Set initial number of hours to be plotted to 144 (6 days)
        self.nightCalc = False  # Determines if DW score is calcuated for nighttime hours (glow disc play)
        
        # Call other setup methods as needed
        self.favesExist = self.getFaves()   # If favorites.txt exists, import values to related MainWindow properties
        self.initUI()                       # Set up and kick-off the UI

    def initUI(self):
        CentralLayout = QVBoxLayout()   # Holds all layouts and widgets. Will be applied to the Central Widget of MainWindow

        # Make radio buttons
        self.radioFave = QRadioButton("Use Favorites")
        self.radioFave.setStyleSheet("font-size: 12px; color: #111B69; font-weight: bold")
        self.radioFave.toggled.connect(self.faveToggled)
        self.radioCust = QRadioButton("Use Custom Address")
        self.radioCust.setStyleSheet("font-size: 12px; color: #111B69; font-weight: bold")
        self.radioCust.toggled.connect(self.custToggled)

        radio_group = QButtonGroup(self)
        radio_group.addButton(self.radioFave)
        radio_group.addButton(self.radioCust)

        controlsLayout = QHBoxLayout()  # Holds the 3 control Frames: Favorites, Custom and Launch
        # Make the Favorites box
        favoritesLayout = QVBoxLayout()
        faveTopLayout = QHBoxLayout()       # Holds the Faves radio button and the Faves Label
        if self.favesExist:
            self.faveLabel = QLabel("Favorites File Found")
        else:
            self.faveLabel = QLabel("Favorites File Not Found...")
        self.faveLatLonLabel = QLabel(" ")
        self.faveCombo = QComboBox(self)
        self.faveCombo.setEditable(True)
        font = self.faveCombo.font()
        font.setPointSize(10)
        self.faveCombo.setFont(font)
        self.faveCombo.lineEdit().setPlaceholderText("--Select a favorite course--")
        self.faveCombo.lineEdit().setReadOnly(True)
        if self.favesExist:
            for key in self.faves:
                self.faveCombo.addItem(key)
        self.faveCombo.setCurrentIndex(-1)
        self.faveCombo.setEnabled(False)    # Wait for fave radio button to be selected to enable
        self.faveCombo.activated.connect(self.aFaveWasSelected)
        
        faveTopLayout.addWidget(self.radioFave)
        faveTopLayout.addSpacing(50)
        faveTopLayout.addWidget(self.faveLabel)
        favoritesLayout.addLayout(faveTopLayout)
        favoritesLayout.addWidget(self.faveCombo)
        favoritesLayout.addWidget(self.faveLatLonLabel)
        favoritesLayout.addStretch()

        # Make the Custom Address box
        customLayout = QVBoxLayout()        # Top level custom box layout
        custTopLayout = QHBoxLayout()       # Holds the Custom radio button and the Cust Label
        addressForm = QFormLayout()         # Holds the Address form entry items
        custButtonLayout = QHBoxLayout()    # Holds the GetGeo and SaveFaves buttons
        
        self.custLabel = QLabel("Enter Address")
        self.submitBtn = QPushButton("Submit Address")
        self.submitBtn.setFixedWidth(130)
        self.submitBtn.setEnabled(False)
        self.submitBtn.clicked.connect(self.submitBtnClicked)
        # Style the GeoBtn here

        self.saveFavesBtn = QPushButton("Save to Faves")
        self.saveFavesBtn.setFixedWidth(100)
        self.saveFavesBtn.setEnabled(False)
        self.saveFavesBtn.clicked.connect(self.save2Faves)
        # Style saveFavesBtn here
        custButtonLayout.addWidget(self.submitBtn)
        custButtonLayout.addWidget(self.saveFavesBtn)
        
        self.street_input = QLineEdit()
        self.street_input.setFixedWidth(200)
        self.street_input.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        addressForm.addRow("Street:", self.street_input)
        self.street_input.setEnabled(False)
        
        self.city_input = QLineEdit()
        self.city_input.setFixedWidth(175)
        self.city_input.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        addressForm.addRow("City:", self.city_input)
        self.city_input.setEnabled(False)
        
        self.state_input = QLineEdit()
        self.state_input.setFixedWidth(25)
        self.state_input.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        addressForm.addRow("State:", self.state_input)
        self.state_input.setEnabled(False)
        
        self.zip_input = QLineEdit()
        self.zip_input.setFixedWidth(50)
        self.zip_input.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        addressForm.addRow("ZipCode:", self.zip_input)
        self.zip_input.setEnabled(False)
        
        # Assemble the customLayout
        custTopLayout.addWidget(self.radioCust)
        custTopLayout.addSpacing(20)
        custTopLayout.addWidget(self.custLabel)
        customLayout.addLayout(custTopLayout)
        customLayout.addLayout(addressForm)
        customLayout.addLayout(custButtonLayout)
        customLayout.addStretch()

        # Make the Launch box
        launchLayout = QVBoxLayout()
        self.courseLabel = QLabel(f"For: {self.courseName}")
        self.courseLabel.setStyleSheet("font-size: 14px; color: darkgreen; font-weight: bold")
        self.courseLabel.setAlignment(Qt.AlignCenter)
        self.getFcstBtn = QPushButton("Get DiscWeather")
        self.getFcstBtn.setStyleSheet(myStyles.getDWStyle)
        self.getFcstBtn.clicked.connect(self.getFcstClicked)
        self.getFcstBtn.setEnabled(False)
        self.dayLightCheck = QCheckBox("Include Score for Nighttime Hours")
        self.dayLightCheck.clicked.connect(self.dayLightChecked)
        self.hoursSpin = QSpinBox(self, maximum = 156, value=144, minimum=12)
        fnt = self.hoursSpin.font()
        fnt.setPointSize(12)
        self.hoursSpin.setFont(fnt)
        self.hoursSpin.valueChanged.connect(self.hoursSpinValChanged)
        self.replotBtn = QPushButton("Re-Plot")
        self.replotBtn.setStyleSheet(myStyles.rpltStyle)
        self.replotBtn.clicked.connect(self.replotClicked)
        self.replotBtn.setEnabled(False)
        self.hoursLabel = QLabel("Set Number of Hours to Forecast")
        self.hoursLabel.setAlignment(Qt.AlignHCenter)
        self.hoursLabel.setStyleSheet("font-size: 12px; color: blue")
        spinLayout = QHBoxLayout()
        spinLayout.addWidget(self.hoursSpin)
        spinLayout.addWidget(self.replotBtn)
        launchLayout.addWidget(self.getFcstBtn)
        launchLayout.addWidget(self.courseLabel)
        launchLayout.addSpacing(10)
        launchLayout.addWidget(self.hoursLabel)
        launchLayout.addLayout(spinLayout)
        launchLayout.addWidget(self.dayLightCheck)
        launchLayout.addStretch()
        
        # Add control frames to the controlsLayout
        controlsLayout.addSpacing(30)
        controlsLayout.addLayout(favoritesLayout)
        controlsLayout.addSpacing(30)
        controlsLayout.addLayout(customLayout)
        controlsLayout.addStretch()
        controlsLayout.addLayout(launchLayout)
        controlsLayout.addSpacing(100)
        
        # Make the Plot frame
        plotLayout = QVBoxLayout()      # Holds the plot output
        self.sc = MplCanvas(self, width=16, height=14, dpi=100)
        self.sc.setVisible(True)
        self.sc.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        plotLayout.addWidget(self.sc)

        # Make a horizonal line
        hLine = QFrame()
        hLine.setFrameShape(QFrame.HLine)
        #hLine.setFrameShadow(QFrame.Sunken)

        # Make a large plot label
        self.plotName = QLabel(f"DiscWeather Forecast for {self.courseName}")
        self.plotName.setStyleSheet("font-size: 20px; color: black; font-weight: bold")

        # Add the controlsLayout and plotLayout to the Central Layout
        CentralLayout.addLayout(controlsLayout)
        CentralLayout.addWidget(hLine)
        CentralLayout.addWidget(self.plotName)
        CentralLayout.addLayout(plotLayout)
        #CentralLayout.addStretch()

        # Make the Central Widget for display in MainWindow
        CentralWidget = QWidget()               # Make a widget called CentralWidget
        CentralWidget.setLayout(CentralLayout)  # Set the CentralWidget layout to be CentralLayout
        self.setCentralWidget(CentralWidget)    # Set MainWindow's central widget to be CentralWidget
        QApplication.processEvents()

        self.radioFave.setChecked(True)         # This needs to be at the bottom of the InitUI method to ensure all objects are initialized

    # Slots for widgets in Favorites frame
    def faveToggled(self):
        if self.radioFave.isChecked():
            print("Favorites Selected")
            # Save working course data to custom address course data
            self.courseNameC = self.courseName
            self.latC = self.lat
            self.lonC = self.lon
            self.jsonResponseC = self.jsonResponse
            # Restore fave course data to working course data
            self.courseName = self.courseNameF
            self.lat = self.latF
            self.lon = self.lonF
            self.jsonResponse = self.jsonResponseF
            # Update courseLabel
            self.courseLabel.setText(f"For: {self.courseName}")

            if self.favesExist:
                self.faveCombo.setEnabled(True)
                self.faveLatLonLabel.setText(f"Latitude: {self.lat}, Longitude: {self.lon}")
                if self.faveCombo.currentIndex() >= 0:
                    self.courseName = self.faveCombo.currentText()
                    self.lat = float(self.faves[self.courseName][0])
                    self.lon = float(self.faves[self.courseName][1])
                    self.faveLatLonLabel.setText(f"Latitude: {self.lat}, Longitude: {self.lon}")
                    self.courseLabel.setText(f"For: {self.courseName}")
                    self.getFcstBtn.setEnabled(True)

        else:
            print("Faves not Selected")
            self.faveCombo.setEnabled(False)
            self.faveLatLonLabel.setText("  ")
            self.getFcstBtn.setEnabled(False)

    def aFaveWasSelected(self):
        if self.favesExist:
            self.courseName = self.faveCombo.currentText()
            self.lat = float(self.faves[self.courseName][0])
            self.lon = float(self.faves[self.courseName][1])
            self.faveLatLonLabel.setText(f"Latitude: {self.lat}, Longitude: {self.lon}")
            self.courseLabel.setText(f"For: {self.courseName}")
            self.getFcstBtn.setEnabled(True)

    # Slots for widgets in Custom frame
    def custToggled(self):
        if self.radioCust.isChecked():
            print("Custom Selected")
            if self.customAddressValid == True:
                self.getFcstBtn.setEnabled(True)
            # Save working course data to faves course data
            self.courseNameF = self.courseName
            self.latF = self.lat
            self.lonF = self.lon
            self.jsonResponseF = self.jsonResponse
            # Restore custom address course data to working course data
            self.courseName = self.courseNameC
            self.lat = self.latC
            self.lon = self.lonC
            self.jsonResponse = self.jsonResponseC
            # Update courseLabel
            self.courseLabel.setText(f"For: {self.courseName}")

            self.street_input.setEnabled(True)
            self.city_input.setEnabled(True)
            self.state_input.setEnabled(True)
            self.zip_input.setEnabled(True)
            self.submitBtn.setEnabled(True)

        else:
            print("Custom not Selected")
            self.street_input.setEnabled(False)
            self.city_input.setEnabled(False)
            self.state_input.setEnabled(False)
            self.zip_input.setEnabled(False)
            self.submitBtn.setEnabled(False)

    def submitBtnClicked(self):
        street = self.street_input.text()
        city = self.city_input.text()
        state = self.state_input.text()
        zip = self.zip_input.text()
        if street == '' or city == '' or state == '' or zip == '':
            self.custLabel.setText("Incomplete Address")
            return
        elif not state.isalpha() or len(state) != 2:
            self.custLabel.setText("Invalid State Abbreviation")
            return
        elif not zip.isdigit() or len(zip) != 5:
            self.custLabel.setText("Incorrect Zip Code")
            return
        else:
            Zip = int(zip)
            self.custLabel.setText("Address Submitted")
        # Submit to getGeoLocation method
        match, Lt, Ln = self.getGeoLocation(street, city, state, Zip)
        if match:
            self.custLabel.setText("GeoCoding Successful")
            self.customAddressValid = True
            self.courseName = street
            self.lat = Lt
            self.lon = Ln
            self.courseLabel.setText(f"For: {self.courseName}")
            self.saveFavesBtn.setEnabled(True)
            self.getFcstBtn.setEnabled(True)
        else:
            self.custLabel.setText("GeoCoding Failed")
            self.customAddressValid = False
            self.saveFavesBtn.setEnabled(False)

    def getGeoLocation(self, street, city, state, zp):
        '''
        Uses U.S. Census Bureau Geocoding API to get latitude/longitude of the street address params passesd in
        Returns a Boolean indicating successful geocoding of address and latitude / longitude values of address.
        Lat / Lon are in decimal degrees, represented as floats with 4 digits of precision
        '''
        LocBASE = "https://geocoding.geo.census.gov/geocoder/"
        return_type = 'locations'
        search_type = 'address'
        params = {
        'street': street,
        'city': city,
        'state': state,
        'zip': zp,
        'benchmark': 'Public_AR_Current',
        'format': 'json'
        } 

        try:
            response = requests.get(f'{LocBASE}{return_type}/{search_type}', params=params)
        except:
            return False, 0.0, 0.0
           
        if response.status_code == 200:
            jresp = response.json()
            try:
                with open("GeoLocation.json", "w") as f:
                    json.dump(jresp, f, indent=3)
            except:
                print("Failed to write GeoLocation.txt")
            numMatch = len(jresp['result']['addressMatches'])
            if numMatch == 0:
                print("No matching address in US Census database.")
                return False, 0.0, 0.0
            else:
                Lt = jresp['result']['addressMatches'][0]['coordinates']['y']
                Ln = jresp['result']['addressMatches'][0]['coordinates']['x']
                Lat = round(Lt, 4)
                Lon = round(Ln, 4)
                # Confirm lat/lon is within continental U.S.
                if Lat < 49.0 and Lat > 24.54 and Lon < -67.0 and Lon > -124.7:
                    return True, Lat, Lon
                else:
                    print("Latitude and Longitude outside of continental US. Try again.")
                    return False, 0.0, 0.0
        else:
            return False, 0.0, 0.0

    def save2Faves(self):
        wString = f"\n{self.courseName},{self.lat},{self.lon}"
        if not(self.favesExist):
            print("File not found. Creating favorites file.")
            with open("favorites.txt", "w") as f2:
                f2.write("#Alias,Latitude,Longitude")
                f2.write(wString)
                self.favesExist = True
        else:   # Faves does exist
            with open("favorites.txt", "r") as file:
                for line in file:   # 
                    if self.courseName in line:
                        self.custLabel.setText("Location already saved")
                        self.saveFavesBtn.setEnabled(False)
                        return
            with open("favorites.txt", "a") as f:
                f.write(wString)

        print(f"Location added to Favorites as {wString}")
        self.custLabel.setText("Location added to favorites")
        location = (self.lat, self.lon)
        self.faves[self.courseName] = location      # Add new favorite to self.faves
        self.faveCombo.addItem(self.courseName)     # Add new favorite course name to Combo box
        self.saveFavesBtn.setEnabled(False)         # Disable the saveFaves button - our work is done

    # Slots for widgets in Launch frame
    def getFcstClicked(self):
        print("Get DiscWeather Button Selected")
        self.replotBtn.setEnabled(False)
        self.courseLabel.setText("Retrieving data ...")
        self.courseLabel.setStyleSheet("font-size: 14px; color: darkred; font-weight: bold")
        QApplication.processEvents()
        self.getNWSjson()
        self.courseLabel.setText(f"For: {self.courseName}")
        self.courseLabel.setStyleSheet("font-size: 14px; color: darkgreen; font-weight: bold")
        self.updateDWPlot()

    def changeCourseLabel(self, t):
        self.courseLabel.setText(t)

    def replotClicked(self):
        if self.jsonResponse != None:
            self.replotBtn.setEnabled(False)
            self.updateDWPlot()

    def dayLightChecked(self, checked):
        if checked:
            self.nightCalc = True
        else:
            self.nightCalc = False
        if self.jsonResponse != None:
            self.updateDWPlot()

    def hoursSpinValChanged(self):
        self.NUMHRS = self.hoursSpin.value()
        if self.jsonResponse != None:
            self.replotBtn.setEnabled(True)

    # DiscWeather-specific methods
    def getFaves(self):
        # Get favorite locations from 'favorites.txt' if it exists. Check latitude/longitude values.
        self.faves = {}
        try:
            with open("favorites.txt", "r") as f:
                print('File favorites.txt found.')
                for line in f:
                    line = line.strip()
                    if not line.startswith('#') and len(line) != 0:     # Ignore comments and blank lines
                        items = line.split(',')
                        alias = items[0]
                        try:
                            lat = float(items[1])
                        except ValueError:
                            print(f"Latitude value error in favorites.txt for course {items[0]}. Please correct.")
                            sys.exit("Program Ended\n")
                        try:
                            lon = float(items[2])
                        except ValueError:
                            print(f"Longitude value error in favorites.txt for course {items[0]}. Please correct.")
                            sys.exit("Program Ended\n")
                        location = (lat, lon)
                        self.faves[alias] = location
                #print(self.faves)
                return True
        except FileNotFoundError:
            print("No favorites found.")
            return False

    def getNWSjson(self):
        # U.S. Weather Service API queries
        # See: https://www.weather.gov/documentation/services-web-api#/default/gridpoint_stations for API documentation
        BASE_URL = "https://api.weather.gov/points/"

        Lat = str(self.lat)
        Lon = str(self.lon)
        url = BASE_URL + Lat + ',' + Lon

        try:
            resp = requests.get(url)
        except:
            sys.exit(f"NWS Points query using {self.lat}, {self.lon} failed. Exiting program.")
        if resp.status_code == 200:
            jresp = resp.json()
            FcstURL = jresp["properties"]["forecastHourly"]
        else:
            sys.exit(f"NWS Points query using {self.lat}, {self.lon} failed. Exiting program.")
        
        # If you get here, then you have a valid URL for the hourly forecast of specified location.
        sleep(1)
        print(f"Retrieving Hourly Forecast for {self.courseName} at {self.lat}, {self.lon} using:")
        print(FcstURL)
        print()

        try:
            self.jsonResponse = requests.get(FcstURL).json()
        except:
            sys.exit(f"NWS Hourly Forecast query using {FcstURL} failed. Exiting program.")
        
        # Save the hourly forecast json to a file
        with open("newForecast.json", "w") as f:
            json.dump(self.jsonResponse, f, indent=3)

    def getDWData(self):
        # Extract data from fcstJSON for the number of datapoints set by config.numHours
        self.temp = []
        self.wind = []
        self.precip = []
        self.dayTimeMask = []
        self.hours = []
        self.scores = []
        for i in range(self.NUMHRS):
            period = self.jsonResponse["properties"]["periods"][i]
            t = period["temperature"]
            self.temp.append(t)
            p = period["probabilityOfPrecipitation"]["value"]
            self.precip.append(p)
            d = period["isDaytime"]
            self.dayTimeMask.append(d)
            dts = parser.parse(period["startTime"][:19])
            self.hours.append(dts)
            windStr = period["windSpeed"]
            w1 = windStr.split(' ')
            w = int(w1[0])
            self.wind.append(w)
            self.scores.append(self.getScore(t,w,p,d or self.nightCalc)) #'d or self.nightCalc' lets setting override daylight info in forecast data
            #self.scores.append(50)

    
    def getScore(self,temp, wind, precip, daylight):
        '''
        Calculates relative contribution levels for temperature, wind and precipitation to the overall
        DiscWeather Quality Index based on settings / thresholds and returns a Quality Index value as a float. 
        '''
        MaxTScore = dwConfig.MaxTScore
        MaxWScore = dwConfig.MaxWScore
        MaxPScore = dwConfig.MaxPScore
        
        # Weather parameter thresholds for calculating DiscWeather scores
        LoT = dwConfig.LoT        # Below which temp score will be 0. Above which score increases to max at MidLoT.
        MidLoT = dwConfig.MidLoT  # Above which temp score will be max until MidHiT
        MidHiT = dwConfig.MidHiT  # Above which temp score decreases to 0 at HiT
        HiT = dwConfig.HiT        # Above which temp score will be 0
        LoW = dwConfig.LoW        # Below which wind score will be Max. Wind score attenuates to 0 at HiW.
        HiW = dwConfig.HiW        # Above which wind score will be 0
        LoP = dwConfig.LoP        # Below which precip score will be Max. Precip score attenuates to 0 at HiP.
        HiP = dwConfig.HiP        # Above which precip score will be 0
        
        # Calculate DiscWeather Quality Index:
        if dwConfig.daylightOnly and not daylight:
            return 0
        
        # Temp Score Calculation:
        d1 = temp - LoT
        span1 = MidLoT - LoT
        d2 = temp - MidHiT
        span2 = HiT - MidHiT
        if temp < LoT:
            return 0
        elif temp >= LoT and temp < MidLoT:
            tscore = MaxTScore * (d1/span1)
        elif temp >= MidLoT and temp < MidHiT:
            tscore = MaxTScore
        elif temp >= MidHiT and temp <= HiT:
            tscore = MaxTScore - (MaxTScore*(d2/span2))
        elif temp > HiT:
            return 0

        # Wind Score Calculation:
        w = wind - LoW
        wspan = HiW - LoW
        if wind <= LoW:
            wscore = MaxWScore
        elif wind > LoW and wind <= HiW:
            wscore = MaxWScore - (MaxWScore *(w/wspan))
        else:
            return 0

        # Precipitation Score Calculation:
        p = precip - LoP
        pspan = HiP - LoP
        if precip <= LoP:
            pscore = MaxPScore
        elif precip > LoP and precip <= HiP:
            pscore = MaxPScore - (MaxPScore *(p/pspan))
        else:
            return 0

        return tscore + wscore + pscore     # Return overall Quality Index

    def updateDWPlot(self):
        # Get data for selected course and lat/lon
        self.getDWData()
        self.plotName.setText(f"DiscWeather Forecast for {self.courseName}")
        # Clear the plots
        self.sc.axes[0].clear()
        self.sc.axes[1].clear()
        self.sc.axes[2].clear()
        self.sc.axes[3].clear()


        # Plot new data
        self.sc.axes[0].plot(self.hours, self.temp, color='blue', marker='o', markersize=4, linestyle='-')
        self.sc.axes[0].set_title('Hourly Temperature Forecast')
        self.sc.axes[0].set_ylabel('Temperature(F)')
        self.sc.axes[0].grid(True, which='major', color='lightgray')
        self.sc.axes[0].axhline(y = dwConfig.LoT, color='red', linestyle='--')
        if min(self.temp) >= 25 and max(self.temp) <= 100:
            self.sc.axes[0].set_ylim(25,100)
            self.sc.axes[0].axhline(y = dwConfig.HiT, color='red', linestyle='--')
        elif max(self.temp) > 100:
            self.sc.axes[0].axhline(y = dwConfig.HiT, color='red', linestyle='--')

        self.sc.axes[1].plot(self.hours, self.wind, color='green', marker='o', markersize=4, linestyle='-')
        self.sc.axes[1].set_title('Hourly Wind Forecast')
        self.sc.axes[1].set_ylabel('Wind Speed(mpH)')
        self.sc.axes[1].grid(True, which='major', color='lightgray')
        self.sc.axes[1].axhline(y = dwConfig.HiW, color='red', linestyle='--')
        
        self.sc.axes[2].plot(self.hours, self.precip, color='black', marker='o', markersize=4, linestyle='-')
        self.sc.axes[2].set_title('Hourly Precipitation Forecast')
        self.sc.axes[2].set_ylabel('Chance of Precipitation(%)')
        self.sc.axes[2].grid(True, which='major', color='lightgray')
        self.sc.axes[2].axhline(y = dwConfig.HiP, color='red', linestyle='--')

        self.sc.axes[3].fill_between(self.hours, 0, self.scores, alpha=0.7)
        self.sc.axes[3].set_title('DiscWeather Quality Index')
        self.sc.axes[3].set_xlabel('Powered by the U.S. National Weather Service Web API', loc='right', size='large', weight='normal', style='italic')
        self.sc.axes[3].set_ylabel('Weather Quality(1-100)')
        self.sc.axes[3].tick_params(axis='x', which='major', labelsize=8, colors='b')
        self.sc.axes[3].tick_params(axis='x', which='minor', labelsize=6)
        self.sc.axes[3].grid(True, which='major', color='lightgray')
        self.sc.axes[3].set_axisbelow(True)

        self.sc.axes[3].set_ylim(0,100)
        self.sc.axes[3].xaxis.set_major_locator(mdates.HourLocator(byhour=0))
        self.sc.axes[3].xaxis.set_major_formatter(mdates.DateFormatter('%a %d'))
        self.sc.axes[3].xaxis.set_minor_locator(mdates.HourLocator(byhour=range(24)))
        self.sc.axes[3].xaxis.set_minor_formatter(mdates.DateFormatter('%I:%M%p'))
        for label in self.sc.axes[3].get_xticklabels(which='both'):
            label.set(rotation=90, horizontalalignment='center')

        #self.sc.fig.suptitle(f"DiscWeather Forecast for {self.courseName}", x=0.05, y = 0.98, horizontalalignment='left', weight='bold', size='x-large')

        # Draw the canvas and make it visible
        self.sc.draw()
        self.sc.setVisible(True)
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()