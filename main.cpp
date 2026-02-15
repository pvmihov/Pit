#include<iostream>
#include <cstring>
#include<filesystem>
std::string command_list[7]={
    "init", "add", "commit", "log", "retrieve", "checkout", "status"
};
int main(int argc, char* argv[])
{
    std::filesystem::path current_path = std::filesystem::current_path();
    std::string current_path_string = current_path.string();
    if (argc==1)
    {
        std::cout<<"No command found\nEnter one of:\n";
        for (std::string command : command_list)
        {
            std::cout<<command<<"\n";
        }
        return 0;
    }   
    if (strcmp(argv[1],"init")==0)
    {
        if (argc!=2)
        {
            std::cout<<"Incorrect number of arguments.\n";
            return 0;
        }
        std::cout<<"I am about to do an init in "<<current_path_string<<"\n";
    }
    else if (strcmp(argv[1],"add")==0)
    {
        if (argc!=3)
        {
            std::cout<<"Incorrect number of arguments.\n";
            return 0;
        }
        std::filesystem::path file_path = current_path / argv[2];
        std::cout<<"I am about to try add with "<<file_path.string()<<"\n";
    }
    else if (strcmp(argv[1],"commit")==0)
    {
        if (argc!=2)
        {
            std::cout<<"Incorrect number of arguments.\n";
            return 0;
        }  
        std::cout<<"I am about to do a commit in "<<current_path_string<<"\n";     
    }
    else if (strcmp(argv[1],"log")==0)
    {
        if (argc!=2)
        {
            std::cout<<"Incorrect number of arguments.\n";
            return 0;
        }  
        std::cout<<"I am about to do a log in "<<current_path_string<<"\n";     
    }
    else if (strcmp(argv[1],"retrieve")==0)
    {

    }
    return 0;
}