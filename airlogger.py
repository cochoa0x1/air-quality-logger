from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Float, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
import datetime
from sqlalchemy.orm import sessionmaker

from pykoreaqi import AirKorea

from time import sleep

import os
import math

DB_FILE_NAME = os.environ["DATABASE_URL"]

#DB_FILE_NAME = 'air.db'

#engine = create_engine('sqlite:///%s'%DB_FILE_NAME, echo=False)
engine = create_engine(DB_FILE_NAME, echo=False)
Base = declarative_base()

class Station(Base):
    __tablename__ = 'stations'
    
    id = Column(Integer, primary_key = True)
    name = Column(String)
    address = Column(String)
    lat = Column(Float)
    long = Column(Float)
    
    measurements = relationship("Measurement", back_populates="station", order_by="Measurement.t")
    
    def __repr__(self):
        return "<Station(name='%s', address='%s')"%(self.name, self.address)
    
    
class Measurement(Base):
    __tablename__ = 'measurements'
    
    id = Column(Integer, primary_key = True)
    
    station_id = Column(Integer, ForeignKey('stations.id'))
    metric = Column(String)
    t = Column(DateTime)
    value = Column(Float)
    
    station = relationship("Station", back_populates="measurements")
    
try:
    Base.metadata.create_all(engine)
except:
    print('tables aleady exist?')



def add_to_database(row,Session):
    
    session = Session()
    
    #first check if our station is already added (assuming unique name/address)
    name, address = row['STATION_NAME'], row['STATION_ADDR']
    
    station = session.query(Station).filter(Station.name == name).filter(Station.address == address).first()
    
    if station is None:
        station = Station(name=name, address = address, lat = x['DM_X'], long = x['DM_Y'])
        session.add(station)
        
    #now go through the measurements
    for m in row['MEASUREMENT']:
        
        #skip if bad value
        value = m['VALUE']
        if not value.replace('.','').isnumeric():
            continue
        
        #fix the date
        t = datetime.datetime.strptime(m['DATA_TIME'],'%Y년 %m월 %d일 %H시')
        
        station.measurements.append(Measurement(metric=m['METRIC'], t =t, value=value ))
    
    session.commit()

while True:
    retry_factor = 1
    base_dt = 30*60
    retry_dt = 60
    try:
        print('getting data...')
        aqi = AirKorea() #checkout kweather also

        data = aqi.get_all_realtime(delay=1,metrics=['PM25'])
        print('found %i stations'%len(data))

        Session = sessionmaker(bind=engine)

        for x in data:
            add_to_database(x,Session)

        print('sleeping...')
        retry_factor =1
        sleep(base_dt)
    except Exception as e:
        print('something failed, waiting to retry')
        retry_factor+=1 
        sleep(math.pow(retry_dt,retry_factor))



