## Authentication and Authorization Project on FastAPI


This project is a web application implementing a user authentication and authorization system with different roles based on FastAPI and a PostgreSQL database. 
The application allows users to register, log in, create, view, and delete posts. 
Access to application functionality is managed based on user roles: admin, manager, and user.

### Functionality

##### User Registration

•	Users can register with the default role user.

•	Passwords are stored in the PostgreSQL database in encrypted form using the bcrypt library.

##### Authentication

•	JWT tokens are used for user authentication.

•	Tokens are stored in cookies with the HttpOnly flag to protect against XSS attacks.

•	Protection against CSRF attacks is implemented using CSRF tokens generated and verified with the itsdangerous library.

##### Authorization

•	Access control is implemented based on user roles.

Roles:

•	admin: full access to all functions, including deleting any posts.

•	manager: can manage user posts except for posts created by administrators.

•	user: can create and delete only their own posts.

##### Post Management
•	Users can create new posts.

•	Posts contain a title, text, author’s name, and creation time.

•	Ability to view a list of posts and detailed view of each post.

•	Deleting posts in accordance with the user’s access rights.

##### Security
•	Passwords are stored in encrypted form using bcrypt.

•	Access tokens (access_token) are stored in HttpOnly cookies.

•	Protection against CSRF attacks is implemented.

•	Access to routes is restricted according to the user’s role.

•	Use of secure cookies when working over the HTTPS protocol.

### Technologies

•	FastAPI: main framework for developing the web application.

•	PostgreSQL: relational database for storing users and posts.

•	Jinja2: for HTML page templating.

•	Databases: asynchronous work with the database.

•	Asyncpg: driver for working with PostgreSQL.

•	JWT (JSON Web Tokens): for user authentication.

•	bcrypt: for password hashing.

•	itsdangerous: for generating and verifying CSRF tokens.

•	python-dotenv: for loading environment variables from the .env file.


### Implementation Details

##### Authentication

User Registration:

•	When registering, the user enters a username and password.

•	The password is hashed using bcrypt and stored in the PostgreSQL database.

•	The user’s role is set to user by default.

#### Login:

•	The user enters a username and password.

•	The entered password is checked against the hash in the database.

•	Upon successful authentication, a JWT token is generated containing information about the user and their role.

•	The token is stored in a cookie with the HttpOnly flag to protect against XSS attacks.

#### JWT Tokens:

•	Used to store user information.

•	Contain username, role, and expiration time exp.

•	Signed with the secret key SECRET_KEY.

#### Authorization

Role-Based Access Control:

•	The role_dependency dependency is used to check the current user’s role.

•	Access to certain routes is restricted depending on the user’s role.

Example of access restriction:

````
@app.get("/admin/tools", response_class=HTMLResponse)
async def admin_tools(request: Request, current_user: dict = Depends(role_dependency(["admin"]))):
````

Permission Checking When Deleting Posts:

•	Admin can delete any posts.

•	Manager cannot delete posts created by administrators.

•	User can delete only their own posts.

#### CSRF Protection

CSRF Token Generation:

•	The itsdangerous library is used for generating and verifying CSRF tokens.

•	A CSRF token is generated when displaying forms and stored both in a cookie and in a hidden form field.

CSRF Token Verification:

•	When submitting a form, the token in the form and the cookie are compared, as well as their validity.

•	If the tokens do not match or are invalid, an HTTP 403 error is returned.

#### Cookie Management

Cookie Security:

•	Cookies are set with the HttpOnly and SameSite=Strict parameters to protect against XSS and CSRF attacks.

•	In production, cookies are set with the secure=True parameter, which means they will only be transmitted over HTTPS.

•	The secure parameter is managed by the IS_PRODUCTION environment variable.

Example of Setting a Cookie:
````
response.set_cookie(
    key="access_token",
    value=access_token,
    httponly=True,
    secure=IS_PRODUCTION
)
````


### Models and Database

User Model (User):

•	Methods for creating a user, authentication, and retrieving user information.

•	Passwords are stored in encrypted form.

Database Model (FDataBase):

•	Methods for working with posts: adding, retrieving, deleting.

•	Posts store information about the title, text, author, and creation time.

#### Template Structure

•	Jinja2 Templates are used for rendering HTML pages.

•	Templates contain forms with CSRF protection.

•	The interface is adapted for different user roles, displaying the appropriate navigation elements and functions.

### Cookie Protection When Connecting via HTTPS

•	When setting cookies, the secure parameter is used, which instructs the browser to transmit the cookie only over a secure HTTPS connection.

•	In the application, the secure parameter is set dynamically based on the IS_PRODUCTION environment variable.

•	In production (IS_PRODUCTION=True), cookies are set with secure=True, providing additional protection of user data.

•	In development (IS_PRODUCTION=False), cookies are set without the secure parameter, allowing the application to be tested without HTTPS setup.

### Conclusion

This project showcases the implementation of an authentication and authorization system using modern approaches and libraries. 
By utilizing JWT for session management, role-based access control, and CSRF protection, the application ensures both security and flexibility. 
The integration with a PostgreSQL database allows for robust data storage and retrieval. 
The use of secure cookies when connected via HTTPS adds an extra layer of security, safeguarding sensitive user information during transmission. 
Overall, this application serves as a solid foundation for building secure web services that require user authentication and role-based authorization.