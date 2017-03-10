# fibrkomat

a client for timewatch.co.il (working hours tracking system)
the client fill the entire month working days

## install & usage
- git clone git@github.com:elasti-rans/fibrkomat.git
- cd fibrkomat
- pip install -r requirements.txt
- ./fibrkomat.py company_number user_number password

## cli
- working time start can be provided, by default its 09:30
- exit time is caclculated by start time + needed working hours for each day

## config file
- a config file can be created at ~/fibrkomat.conf
- config file is a way to add a flags/ args to cli automatically
- format of config is single line with same syntax as clli
- config content example: "company user password -s 36000"
