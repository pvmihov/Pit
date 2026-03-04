# Project Pit

Pit is a version control system (VCS), made as a learning project in
- python path manipulation and heshing
- embedding python inside c++ 
- the concept behind git
- basic server communication in python and node.js

Currently the project only supports Linux

# Setting up pit

To set up pit, we need the following steps:
1. Either clone the repository, or install main.cpp, path_logic.py and communicator.py in the same folder and navigate to the folder
2. Open main.cpp and add the full path of the installation folder in the string called install_folder
3. Run the following command to install python3 dev for embedding
```bash
sudo apt-get install python3-dev
```
4. Compile main.cpp with the neccessary python descriptions.
```bash
g++ main.cpp -o pit $(python3-config --cflags --embed --libs)
```
5. Add the newly created file to the path
```bash
sudo cp pit /usr/local/bin
```

# Server simulation

pit doesn't actually support network features. When using clone, fetch, pull or push, it contacts a localhost listener, running on the same computer, and communicates with it.
To turn on the "server" you have to run the run_server.js file
```bash
node run_server.js
```
The program will prompt you to select a directory, where all the "network" data of the repository will be stored. After that you will be prompted to choose a listening port. When the "server" is running, you need to enter that port number to the pit commands, so it can contact the "server".
