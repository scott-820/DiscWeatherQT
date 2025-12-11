# Collection of styles for the DiscWeather PyQt App

getDWStyle = """
            QPushButton {
                background-color: #4CAF50; /* Green background */
                color: white; /* White font color */
                font-size: 18px; /* Font size */
                width: 150px; /* Button width */
                height: 30px; /* Button height */
                border-radius: 3px; /* Rounded corners */
            }
            QPushButton:disabled {
                background-color: #E0E0E0;
                color: grey
            }
            QPushButton:hover {
                background-color: #45a049; /* Darker green on hover */
            }
        """

rpltStyle = """
            QPushButton {
                background-color: blue;
                color: white; /* White font color */
                font-size: 16px; /* Font size */
                width: 50px; /* Button width */
                height: 30px; /* Button height */
                border-radius: 7px; /* Rounded corners */
            }
            QPushButton:disabled {
                background-color: #E0E0E0;
                color: grey
            }
            QPushButton:hover {
                background-color: darkblue;
            }
        """
#print(getDWStyle)