@echo off

docker stop $(docker ps -q)
timeout /t 20

docker rm $(docker ps -aq)
timeout /t 10

docker network rm court_network
timeout /t 5

echo "Projects and apps created successfully!"