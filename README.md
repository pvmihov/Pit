Project Pit

Pit is a lighter version of git, build from scratch, as an exercise and a learning tool. 

Current list of commands
sudo apt-get install python3-dev
g++ main.cpp -o pit $(python3-config --cflags --embed --libs)
sudo cp pit /usr/local/bin