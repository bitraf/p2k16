# Userstories
Userstories describes what the user requires from a function in the system

## User management
### Register a new user ( open to public )
- A user sends in th following information:
  - Username (username)
  - First name (first_name)
  - Last name (last_name)
  - Email (email)
  - Phone number (phone)
  - Password (password)
  - Member type (member_type)
- The system then checks if the username or email is not in the database.
  If it is, then the system will abort and return HTTP 409 Conflict and a json body like this:
  `{ 'status':'409', 'message':'username|email already exist'  }.
- The system saves the data to the database in the user table and returns HTTP 201 and a json body like this:
  `{ 'status': '201', 'username': 'myuser', 'first_name': 'first name', 'last_name': 'last name', 'email': 'my@email.com', 'member_type': 'Member type' }`
  

### Update userdata on a user ( you can update you own or some one with admin rights an update anyones data )
- A user sends the fields he wants to update and a auth token to authenticate his user.
  If username is sent in and the token has admin rights, then the system will get the username to update information on from that username instead of the username from the token.
  If the username is a valid username in the database, then a HTTP 404 and a json body of `{ 'status': '404', 'message': 'not found.'}`
- The system then takes the fields that is submitted in and updates the record in the database to the user specified by username. 
  

### Authenticate a user ( open to public )
- The user submits his username and password in to the system
- The systems verifies that the password is the correct one for that user and returns a oauth2 bearer token.
- If its the wrong password, the system will return HTTP 401 and a json body of  `{ 'status': '401', 'message': 'Access denied' }`

### Get global user statistics
- Returns numbers of users in total and for each member_type

## Role management
### Set role on a user ( anyone with admin rights )
- The user submits a json body with the username and which role the user should have: `{'user': 'my_username', 'group': 'my_new_group'}`
- Check if user is admin, see operation:verify_admin below
- If the role does not exist, the system returns HTTP 404 and and a json body of `{ 'status': '404', 'message': 'not found.'}`
- The system then creates a user-role entry and returns HTTP 201 and a json body like:
  `{ 'status': '201', 'message': 'Role added' }`

### Remove role ( anyone with admin rights )
- The user submits a json bode with username and role combination to remove: `{'user': 'my_username', 'group': 'group to remove'}`
- Check if user is admin, see operation:verify_admin below
- If the role does not exist, the system returns HTTP 404 and and a json body of `{ 'status': '404', 'message': 'not found.'}`
- The system then removes the user-role entry and returns HTTP 201 and a json body like:
  `{ 'status': '201', message: 'Role removed' }`

### Create role ( anyone with admin rights )
- Check if user is admin, see operation:verify_admin below
- If the role does not exist, the system returns HTTP 404 and and a json body of `{ 'status': '404', 'message': 'not found.'}`
- The system then removes the user-role entry and returns HTTP 201 and a json body like:
  `{ 'status': '201', message: 'Role removed' }`

### List roles  ( anyone with admin rights )
- Check if user is admin, see operation:verify_admin below
- Returns HTTP 200 and body with a json array over the available roles:
  `{
  'name':'role_1', 'description':'role description 1',
  'name':'role_2', 'description':'role description 2',
  'name':'role_3', 'description':'role description 3'
  }`



### List users with role  ( anyone with admin rights )
- The user posts a username as a json body: `{'username': 'my_user'}`
- Check if user is admin, see operation:verify_admin below
- Returns HTTP 200 and body with a json array over the available roles:
  `{
  'name':'role_1', 'description':'role description 1',
  'name':'role_2', 'description':'role description 2',
  'name':'role_3', 'description':'role description 3'
  }`


## Common operations

### Check if user is admin ( operation:verify_admin )
- The system authenticates the user token as admin, it the user is not a admin, the system will return HTTP 401 and a json body of  `{ 'status': '401', 'message': 'Access denied' }`