import datetime


today = datetime.date.today()
today_date_month = today.strftime('%d.%m')
today_year = int(today.strftime('%Y'))
current_time = datetime.datetime.now().time()
formatted_time = current_time.strftime("%H:%M")

current_year = datetime.date.today().year

#time_start = datetime.timezone
