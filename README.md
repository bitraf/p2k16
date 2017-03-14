# p2k16

## Deployment

### Docker-compose deployment
The docker-compose setup contains both the flask app and the required services.

To build and deploy the full service, run the following commands.
- Clone the project
```
git clone https://github.com/bitraf/p2k16.git
cd p2k16
```
- Build the docker-compose services
```
docker-compose build
```
- Deploy services
```
docker-compose up -d
```