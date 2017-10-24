from __future__ import print_function
import os
import psycopg2
import datetime
from pykoreaqi import AirKorea
from time import sleep
import math


#lets remove the need to use pandas
def read_sql(sql,cn,params=[]):
	with cn.cursor() as cr:
		cr.execute(sql,params)
		columns = [col[0] for col in cr.description]
		data = [ dict(zip(columns,[str(r) for r in row])) for row in cr.fetchall()]
	return data

db = os.environ['DATABASE_URL']

print('getting station cache...')
cn = psycopg2.connect(db)

db_stations = read_sql('select id, name from stations',cn)
STATION_CACHE = dict( (s['name'],s['id']) for s in db_stations )
cn.close()

retry_factor = 1
base_dt =60*60
retry_dt = 60

headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}

while True:
	
	try:
		print('getting data...')
		aqi = AirKorea(headers=headers) #checkout kweather also

		data = aqi.get_all_realtime(delay=1,metrics=['PM25'])
		print('found %i stations'%len(data))

		stations = [ r['STATION_NAME'] for r in data]
		measurements = [ r['MEASUREMENT'] for r in data]

		all_ms=[]
		for sname,ms in zip(stations,measurements):
			for m in ms:
				if not m['VALUE'].replace('.','').isnumeric():
					continue
				if sname not in STATION_CACHE:
					continue
					
				t = datetime.datetime.strptime(m['DATA_TIME'],'%Y년 %m월 %d일 %H시')
				st_id = STATION_CACHE[sname]
				all_ms.append([st_id,m['METRIC'],t,m['VALUE']])

		print('adding to db')
		cn = psycopg2.connect(db)
		cr = cn.cursor()
		cr.executemany('insert into measurements(station_id,metric,t,value)values(%s,%s,%s,%s)',all_ms)
		cn.commit()
		cn.close()

		print('sleeping...')
		retry_factor =1
		sleep(base_dt)
	except Exception as e:
		print('something failed, waiting to retry')
		print(e)
		retry_factor+=1 
		sleep(math.pow(retry_dt,retry_factor))