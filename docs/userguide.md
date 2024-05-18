User Guide
Installation
To install the Mushroom App, you will need to have Node.js and MongoDB installed on your system.

Once you have installed the prerequisites, you can clone the Mushroom App repository and run the following commands:

npm install
npm start
Configuration
The Mushroom App can be configured by modifying the config.json file. The following options are available:

port: The port that the Mushroom App will listen on.
mongodb_uri: The URI of the MongoDB database.
Usage
To use the Mushroom App, you can either visit the website at localhost:3000 or use the API directly.

To use the website, simply enter your search criteria into the search bar and click the "Search" button. The website will display a list of mushrooms that match your search criteria.

To use the API, you can make a GET request to the /mushrooms endpoint. The API will return a list of all mushrooms in the database.
