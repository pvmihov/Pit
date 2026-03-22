g++ main.cpp -o pit $(python3-config --cflags --embed --libs)
sudo cp pit /usr/local/bin