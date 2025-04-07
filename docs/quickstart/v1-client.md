# GMX Arbitrage Client
The v1 client is our first client that interface with the engine.

This client was built in order to win a grant from [GMX](https://gmx.io).

This engine is located in the `backend-flask-server` branch and hosted temporarily (running on free AWS credits) on the web at `https://fundingratesniper.com`.

### Starting the client locally
`git clone git@github.com:PrabodhGyawali/GMX-Arb-UI.git`

`cd GMX-Arb-UI`

`npm install`

`npm start`

This should allow you to use the repo in the browser.

### Starting the `backend-flask-server` version of the engine
`git clone https://github.com/50shadesofgwei/funding-rate-arbitrage -b backend-flask-server gmx-engine`

`cd gmx-engine`

##### Install dependencies in your python environment
`pip install -e .`

`mv example.env .env`

`project-run-ui`


