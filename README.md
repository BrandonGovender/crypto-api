# How to Run Crypto-Api using Docker
This Project is written in Python. It is the backend to crypto-app https://github.com/BrandonGovender/crypto-app.
It requires an IDE, like VS Code, and a docker engine on your machine. Commands included for containerizing and running crypto-app as well as crypto-api

## Description
A websocket is connected to valr-full-orderbook-update endpoint and an up to date orderbook is kept in memory to find the best buying bid based on inputted USDT.

## Commands to run

1. After clonning both projects in your preffered directory, you can open up the crypto-api in VS Code

2. Open your terminal and make sure you are rooted in your crypto-api directory

3. With your docker engine running (Docker Desktop), run:

### `docker build . -t crypto-api`

This will create your crypto-api image after a moment.

4. Open your crypto-app in VS Code and run the ffg in a new terminal:

### `docker build . -t crypto-app`

Similarly this will build your crypto-app image.

5. Since our app server will be talking to our backend on your local machine, we will require a bridge in docker. Run:

### `docker network create channel`

This will create a channel that you can use to have your containers communicate with each other. 'channel' can be replaced with any other name.

6. In your crypto-api terminal run: 

### `docker run --name crypto-api --rm --network channel -p 8000:8000 crypto-api`

This begins your backend container and exposes port 8000 to itself.

7. In your crypto-app terminal run: 

### `docker run --rm --name crypto-app --network channel -p 3000:3000 crypto-app`

This allows you to connect to the app server from http://localhost:3000/.

8. To close either servers, goto your respective terminal and escape using 'ctrl + c' 

## API Swagger
The FastAPI swagger can be accessed via http://localhost:8000/docs#/

### /api/get_coin_list 

This will return the MemeCoin list which calls up https://api.binance.com/api/v3/depth. This function also converts the returned USDT to ZAR in its response.

### /api/balance_index

This call will use the MemeCoin list if POST header is left empty or None. You can also pass your own list like the below:

[
  {
    "symbol": "BTC",
    "mcap": 20000,
    "price": 50
  },
  {
    "symbol": "ETH",
    "mcap": 10000,
    "price": 25
  },
  {
    "symbol": "LTC",
    "mcap": 5000,
    "price": 10
  }
]

Please note that price will have to be converted to zar. The /api/get_zar call can do this by passing in the 'mcap' as quantity.

'asset_cap' is from 0 -> 1. Cap limits <= 0 or >= 1 is treated as unlimited percent.

'total_capital' must be in zar.