## install dependencies

`pip3 install -r requirements.txt`

## set flask environment variables 

set the port to run the app in `.env` under FLASK_RUN_PORT= \
make sure FLASK_APP points to the entry file of the app 

## start the app on your network

`flask run --host=<your private ip>`

upon startup, the following UDP events run automatically:
- broadcast HELLO?
- wait 5s for response
- retry after 10s 

if no response is received, the component becomes SOL and:
- generates its own STAR_UUID
- adds itself to its list of components 
- starts a new thread to listen for UDP broadcasts
- becomes available for TCP/http requests on the same port eg. `Running on http://192.168.1.21:8013`

all events up to this point are console logged

## testing TCP
a GET request from another device on the same network to the `/` route returns `Hello World` 


