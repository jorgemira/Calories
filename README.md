# Calories REST API
REST API for the input of calories, Project for Toptal interview of Jorge Mira Yague

## Getting Started
These instructions will get you a copy of the project up and running on your local machine for development and testing 
purposes. 

See [Deployment](#deployment) section for notes on how to deploy the project on a live system.

## Prerequisites
The requirements for this Application are a Linux environment with Python 3.8 installed and pipenv. 

Given the multiplatform nature of Python, it should work on different environments without any major changes, but it has
not been tested

## Installing 
First of all, clone the repository and move to it
```shell script
git clone git@git.toptal.com:screening/jorge-mira-yague.git
cd jorge-mira-yague
```
On a production environment there is no need to install some dependencies, the following command is issued to install
the minimum requirements:
```shell script
pipenv install
```
If this is a development environment, install the whole list of dependencies:
```shell script
pipenv install --dev
```
Once the dependencies are installed, activate the environment:
```shell script
pipenv shell
```

## Environment variables
The application supports external configuration through environment variables, the supported variables and its default
 values if not previously set are:

- **CLS_ENV**: Environment where run the app, it can only take one of the following values: *dev*, *test*, *prod* 
  - Defaults to: *dev*
- **CLS_ADDRESS**: IPv4 Address that the web server will be listening to 
  - Defaults to: *0.0.0.0*
- **CLS_PORT**: Port that the web server will be listening to 
  - Defaults to: *8080*
- **CLS_TOKEN_SECRET_KEY**: Secret string to use when encoding authentication tokens  
  - Defaults to: *secret_string*
- **CLS_TOKEN_LIFETIME_SECONDS**: Lifetime of the authentication tokens, in seconds
  - Defaults to: *1800*
- **CLS_NTX_BASE_URL**: URL of Nutritionix API
  - Defaults to: *https://api.nutritionix.com/v1_1*
- **CLS_NTX_APP_ID**: APP ID for Nutritionix API
  - Defaults to: *29787544*
- **CLS_NTX_API_KEY**: API Key for Nutritionix API
  - Defaults to: *e0ecc4ea5307e6392caba2dd9023085f*
- **CLS_KEYFILE**: Key file for https requests
  - Defaults to: *certs/server.key*
- **CLS_CERTFILE**: Certfile for https requests
  - Defaults to: *certs/server.crt*
- **CLS_CACERTS**: Cacerts file for https requests
  - Defaults to: *certs/ca-crt.pem'*

## Running the tests
To run the tests the development dependencies need to bee installed (see [Installing](#installing)).

From the already initialized pipenv run the following command:
```shell script
(pipenv-env)$ python manage.py test 
```

## Generating code documentation
Sphinx docstrings have been used through the project, so automatic code documentation can be built using Sphinx in html
format for an easier read.

To build the documentation run the following commands from a pipenv environment with
development packages installed (see [Installing](#installing))
```shell script
(pipenv-env)$ cd calories/docs/
(pipenv-env)$ sh create_docs.sh
(pipenv-env)$ firefox build/html/index.html 
```

## Deployment
First of all, the database needs to be initialized, so after setting the right environment variables (see 
[Environment Variables](#environment-variables)), the following command is executed:
```shell script
(pipenv-env)$ python manage.py build_db
```
After the database is built, the app can run using the following command:
```shell script
(pipenv-env)$ python manage.py run
```

## Endpoints created
This is a list the endpoints created by the application with their supported actions and their function:
###​api/login/
- **POST**: Returns an authorization token if the user logged in succesfully
### api/users/
- **GET**: Returns the list of all the users 
- **POST**: Adds a user 
### api/users/*\<username\>*/
- **GET**: Returns the user *username*
- **PUT**: Updates the user *username*
- **DELETE**: Deletes the user *username*
### api/users/\{username\}/meals
- **GET**: Returns the list of meals for the user *'username'*
- **POST**: Adds a meal for the user *'username'*
### api/users/*\<username\>*/meals/*\<id\>*/
- **GET**: Returns the meal with id *'id'* for the user *'username'*
- **PUT**: Updates the meal with id *'id'* for the user *'username'*
- **DELETE**: Deletes the meal with id *'id'* for the user *'username'*
 
All the requests for users and meals need to include the authentication token provided by the login endpoint
 
Detailed documentation on the endpoints, with examples of their use including the possibility of live testing, can be 
found on the UI automatically created on the development environment, accesible through:

http://0.0.0.0:8080/api/ui/

## Pagination and filtering
The endpoints that return a list of elements when a GET request is performed on them ([api/users/](#apiusers) and 
[api/users/\{username\}/meals](#apiusersusernamemeals)) support pagination and filtering. 

The pagination parameters are specified on the query string of the request and have the following names:
- *itemsPerPage*
- *pageNumber*

If the values for the pagination parameters are unspecified, the API uses a default of 10 items per page and returns the
first page

The filtering of the results supports the use of parenthesis, the following relational operators:
- *eq*: equals
- *ne*: not equals
- *gt*: greater than
- *lt*: lower than

And the following boolean operators:
- *or*
- *and*

This is an example of a filtering string:
```
(date eq '2016-05-01') AND ((number_of_calories gt 20) OR (number_of_calories lt 10))
```
The filtering parameter is specified in the query string and has the name *filter*

## Roles
The application uses three different kind of user roles. Its permisions are as follow  
- **USER**: 
  - It can login to the application
  - It must be created by a MANAGER or ADMIN user but it is allowed, to update and delete itself. 
  - It cannot check the user list
  - It has CRUD access to all its meals 
- **MANAGER**: 
  - It can login to the application
  - It must be created by an ADMIN user, and it can only create and update users with role user USER
  - It can update and delete itself
  - It can check the user list
  - It cannot perform any operation for meals
- **ADMIN**: 
  - It can login into the application
  - It is allowed to perform any operation on both users and meals
  - One default admin user is created when the database is built with username *admin* and password *admin1234* 

## Built With
* [Pipenv](https://pipenv-fork.readthedocs.io/) - Virual environment and dependency management
* [Flask](https://flask.palletsprojects.com/) - Web framework
* [Connexion](https://connexion.readthedocs.io/) - HTTP Request handling
* [Gunicorn](https://gunicorn.org/) - WSGI HTTP Server
* [Marshmallow](https://marshmallow.readthedocs.io/) - Object Serialization Framework
* [SQLAlchemy](https://www.sqlalchemy.org/) - SQL toolkit and Object Relational Mapper
* [Sphinx](https://www.sphinx-doc.org/en/master/) - Automatic Documentation generation from docstrings
* [FIQL Parser](https://fiql-parser.readthedocs.io/) - Filter parsing

## Authors

* **Jorge Mira Yague** - [jorgemira](https://github.com/jorgemira/)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
