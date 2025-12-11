
numHours = 144          # Number of hours to plot: (from 12 to 156)
daylightOnly = True     # Set to false to allow night predictions for glow disc play

# Thresholds for calculating hourly DiscWeather scores:

LoT = 40        # Below which overall score will be 0. Above which temp score increases to max at MidLoT.
MidLoT = 70     # Above which temp score will be max
MidHiT = 83     # Above which temp score attenuates to 0 at HiT
HiT = 95        # Above which overall score will be 0
LoW = 5         # Below which wind score will be Max. Wind score attenuates to 0 at HiW.
HiW = 17        # Above which overall score will be 0
LoP = 15         # Below which precip score will be Max. Precip score attenuates to 0 at HiP.
HiP = 50        # Above which overall score will be 0

# Relative contributions for temperature, wind and precipitation to overall score / Quality Factor.
# The total for all 3 must add up to 100.
MaxTScore = 35
MaxWScore = 35
MaxPScore = 100 - (MaxTScore + MaxWScore)
