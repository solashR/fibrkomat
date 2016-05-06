# fibrkomat

a client for timewatch.co.il (working hours tracking system)
the client fill the entire month working days

## install & usage
- pip install requests
- pip install BeautifulSoup
- git clone git@github.com:elasti-rans/fibrkomat.git
- cd fibrkomat
- ./fibrkomat.py company_number user_number password

## warnings
- the client doesn't commit the month, just fill the working hours for all days

## cli
- working time start can be provided, by default its 09:30
- exit time is caclculated by start time + needed working hours for each day
