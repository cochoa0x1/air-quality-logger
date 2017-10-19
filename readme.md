# Log air quality data into sqlite database every hour or so


![alt text](./air.png "map") 


### setup

1. setup postgress docker
```
docker pull postgres
```

2. 
```
pip install -r requirements.txt
```

3. setup database
```
export DATABASE_URL=postgres://postgres:<???>@<???>/<???>
```

4. simple daemon
ctrl+z -> bg
```
disown %1
```

or use nohup/screen/etc