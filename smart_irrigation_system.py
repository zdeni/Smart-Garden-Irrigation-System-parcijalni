import requests
import sys
from requests.models import HTTPError
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile
from PySide6.QtGui import QPixmap
# Even though I get a warning that "QWebEngineView" is not accessedPylance, without this import the "load" method doesent work
from PySide6.QtWebEngineWidgets import QWebEngineView 
from datetime import date, datetime



class Irrigator(QMainWindow):
    
    manual = False
    irrigator_status = False
    locations ={
            "Zagreb":"latitude=45.8144&longitude=15.978&timezone=auto",
            "Buenaventura":"latitude=3.8801&longitude=-77.0312&timezone=auto",
            "London" : "latitude=51.5085&longitude=-0.1257&timezone=auto",
        }
    dates = []
    precipitation_probabilities = []

    def __init__(self):
        super().__init__()

        ui_file = QFile("irrigator.ui")
        loader = QUiLoader()
        self.ui = loader.load(ui_file, self)
        ui_file.close()
        self.setCentralWidget(self.ui)
        self.populate_dropdown(self.locations)

        

        self.ui.humidity_slider_label.setText(f"Soil humidity\nsimulator: {self.ui.humidity_slider.value()}")
        self.ui.manual_control_toggle_button.clicked.connect(self.manual_toggle)
        self.ui.irrigator_on_button.clicked.connect(self.turn_on_irrigation)
        self.ui.irrigator_off_button.clicked.connect(self.turn_off_irrigation)
        self.ui.humidity_slider.valueChanged.connect(self.update_humidity_slider_label)
        self.ui.location_dropdown.currentIndexChanged.connect(self.load_location)
        self.ui.humidity_slider.valueChanged.connect(self.check_if_irrigation_needed)


    def get_forecast(self, coordinates):
        try:
                URL = f"https://api.open-meteo.com/v1/forecast?{coordinates}&daily=precipitation_probability_max"
                response = requests.get(URL)
                response.raise_for_status()

                forecast = response.json()
                return forecast
        
        except HTTPError as e:
            print(e)

    def manual_toggle(self):
        if self.manual == True:
            self.manual = False
            self.ui.irrigator_on_button.setEnabled(False)
            self.ui.irrigator_off_button.setEnabled(False)
            self.ui.manual_control_toggle_button.setText("Manual control is OFF")
        else:
            self.manual = True
            self.ui.irrigator_on_button.setEnabled(True)
            self.ui.irrigator_off_button.setEnabled(True)
            self.ui.manual_control_toggle_button.setText("Manual control is ON")

    def turn_on_irrigation(self):
        self.irrigator_status = True
        self.ui.irrigator_status_display.setText("Irrigation is ON")
        pixmap = QPixmap('sprinkleron.png')
        self.ui.image_label.setPixmap(pixmap)


    def turn_off_irrigation(self):
        self.irrigator_status = False
        self.ui.irrigator_status_display.setText("Irrigation is OFF")
        pixmap = QPixmap('sprinkleroff.png')
        self.ui.image_label.setPixmap(pixmap)


    def update_humidity_slider_label(self):
        self.ui.humidity_slider_label.setText(f"Soil humidity\nsimulator: {self.ui.humidity_slider.value()}%")

    def load_graph(self, link):
        self.ui.web_box.load(link)

    # def check_if_irrigation_needed(self, location):
    #     # dates = data['daily']['time']
    #     # precipitation_probabilities = data['daily']['precipitation_probability_max']

    def populate_dropdown(self, locations):
        for city in locations:
            self.ui.location_dropdown.addItem(city)

    def load_location(self):
        city_coordinates = self.locations[self.ui.location_dropdown.currentText()]
        forecast = self.get_forecast(city_coordinates)
        dates_raw = forecast['daily']['time']
        self.dates = [date[8:10] + '.' + date[5:7] + '.' for date in dates_raw]
        self.load_graph(f"https://quickchart.io//chart?v=2.9.4&c={self.populate_chart(forecast)}")
        self.precipitation_probabilities = forecast['daily']['precipitation_probability_max']
        self.check_if_irrigation_needed()

    def populate_chart(self, forecast):
        
        precipitation_probabilities = forecast['daily']['precipitation_probability_max']
        chart = {'type': 'bar','data': {'labels': self.dates,'datasets': [{
                'type': 'bar',
                'label': 'Maximum daily precipitation probability (%)',
                'data': precipitation_probabilities}]},
                'options':{'plugins':{'datalabels':{
                'anchor':'end','align':'center','backgroundColor': 'white',
                'borderColor': 'rgba(255, 255, 255, 1.0)','borderWidth': 1,'borderRadius': 5,},},'scales': {
                'yAxes': [{'ticks': {'min': 0,'max': 100,'stepSize': 20,},},],},},}
        return (chart)
        
    def check_if_irrigation_needed(self):
        
        if self.is_high_probability_of_precipitation()[0]:
                date = self.is_high_probability_of_precipitation()[1]
                self.turn_off_irrigation()
                self.ui.forecast_textbox.setText(f"High probability of precipitation expected on {self.dates[date]}")
        else:
            if self.manual == False:
                if self.ui.humidity_slider.value() < 76:
                    self.turn_on_irrigation()
                    self.ui.forecast_textbox.setText(f"Low probability of precipitation in the next 7 days.")
                else:
                    self.turn_off_irrigation()
                    self.ui.forecast_textbox.setText(f"Low probability of precipitation in the next 7 days.")
        


    def is_high_probability_of_precipitation(self) -> bool:
        
            for i,probability in enumerate(self.precipitation_probabilities):
                if probability>60:
                    return [True, i]
                
            return [False, None]



def main():
    app = QApplication()
    window = Irrigator()
    window.ui.show()
    window.load_location()
    sys.exit(app.exec())

    



if __name__ == "__main__":
    main()
