##Intro

SimpleOTP is a Python based minimalist one-time password storage/sharing tool.


##Dependencies

- CherryPy framework (3.2.4+)
- pyOpenSSL (0.13.1+) (if SSL is enabled in your config)
- SQLite


##Installation/Configuration

- Modify the "data/app.conf" configuration file to reflect your necessary options
- Checkout the project in the desired directory and simply execute the run.sh script
- If you wish to use the HTTPS protocol, you will have to enable it in the app.conf as well as generate your own key and certificate.
- Ensure that the current user has permissions to modify the content in the directory you're running the app.
- To run the app, simply execute ./run.sh

##License

Copyright 2014 MindGeek, Inc.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.