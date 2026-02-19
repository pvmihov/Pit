#include<iostream>
#include<cstring>
#include<filesystem>
#include<Python.h>
std::string command_list[10]={
    "help", "init", "add", "commit", "log", "restore" ,"retrieve", "checkout", "status", "show"
};
std::string main_info="pit is a version control system (VCS), done as a learning project in python.\nFor help on its specific commands try pit help <command>.\nThe list of commands is:\n";
std::string help_info[10]={
    "Description: help prints a manual for each function in pit.\nFormat: pit help <command_name>",
    "Description: init creates a repository in the directory inside which it is called.\nFormat: pit init\nSpecifics: Will not create a repository if one exists inside the folder, or if the folder is part of a repo.",
    "Description: add stages changes to prepare for next commit and adds them to the index file.\nFormat: pit add <file_name/folder_name>\nSpecifics: If run on a folder, it will stage all the files inside the folder, even deleted ones.",
    "Description: commit creates a new commit containing the current changes in the index and the received message.\nFormat: pit commit",
    "Description: log prints the entire history of commits inside the currently loaded branch.\nFormat: pit log\nSpecifics: Each commit prints its name, message, and brief info on the changes.",
    "Description: restore returns a file to the state it is in the last commit.\nFormat: pit restore <file_name>",
    "Description: retrieve collects a file in the state of a given commit, that has to be inside the current branch.\nFormat: pit <commit_name> <file_name>\n        pit <commit_name> <file_name> <location_name>\nSpecifics: Writing last for the name of the commit takes the last commit.\nThe first option outputs the contents to the console if it is text.\nThe second outputs creates or overwrites the file in location_name to include the information.",
    "Description: switches to a different branch of the repository.\nFormat: pit checkout <branch_name>\nSpecifics: If the branch doesn't exist, it will create it as a copy of the current one and switch. When switching all tracked files will be reverted to the new branch versions, unless there are conflicting changes.",
    "Description: status returns the current status of a file, as a part of the repository.\nFormat: pit status <file_name>\nSpecifics:\n   Untracked: File isnt in the index.\n   Unchanged: File is the same as in the last commit.\n   Changed: File has been changed from the last commit, but hasn't been staged.\n   Staged: File has been changed and staged.",
    "Description: show prints the current information inside the index.\nFormat: pit show\nSpecifics: The index contains the number of files, each file contains a name, blob, two booleans for whether it exists and whether it was staged for a change. Then there is the number of folders and each has a name and a blob."
};
std::string install_folder="/home/petar/Documents/pit";
int callPython(std::string func_name, int numArgs, const char* args[])
{
    Py_Initialize();
    PyRun_SimpleString("import sys");
    std::string append_code = "sys.path.append('"+install_folder+"')";
    PyRun_SimpleString(append_code.c_str());
    PyObject* pName = PyUnicode_FromString("communicator");
    PyObject* pModule = PyImport_Import(pName);
    Py_DECREF(pName);
    if (pModule==nullptr)
    {
        PyErr_Print();
        std::cerr << "Failed to load 'communicator.py'\n";
        return 1;
    }
    PyObject* pFunc = PyObject_GetAttrString(pModule, func_name.c_str());
    if (pFunc==nullptr || !PyCallable_Check(pFunc))
    {
        if (PyErr_Occurred()) PyErr_Print();
        std::cerr<<"Couldn't find _init function in communicator.py";
        Py_DECREF(pModule);
        return 1;
    }
    PyObject* pArgs = PyTuple_New(numArgs);
    for (int q=0;q<numArgs;q++)
    {
        PyObject* curArg = PyUnicode_FromString(args[q]);
        PyTuple_SetItem(pArgs,q,curArg); ///this steal the refrence, so when we decref pArgs, it will decref pathValue
    }
    PyObject* pResult = PyObject_CallObject(pFunc, pArgs);
    if (pResult == nullptr)
    {
        PyErr_Print();
        Py_DECREF(pModule);
        Py_DECREF(pArgs);
        Py_DECREF(pFunc);
        return 1;
    }
    Py_DECREF(pModule);
    Py_DECREF(pArgs);
    Py_DECREF(pFunc);  
    Py_DECREF(pResult);
    std::string cppResult = PyUnicode_AsUTF8(pResult);
    std::cout<<cppResult<<"\n";
    return 0;
}
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
        const char *args[1]={current_path_string.c_str()};
        callPython("_init",1,args);
    }
    else if (strcmp(argv[1],"add")==0)
    {
        if (argc!=3)
        {
            std::cout<<"Incorrect number of arguments.\n";
            return 0;
        }
        std::filesystem::path file_path;
        if (strcmp(argv[2],".")!=0) file_path = current_path / argv[2];
        else file_path = current_path;
        std::string file_string = file_path.string();
        const char *args[2]={current_path_string.c_str(),file_string.c_str()};
        callPython("_add",2,args);
    }
    else if (strcmp(argv[1],"commit")==0)
    {
        if (argc!=3)
        {
            std::cout<<"Incorrect number of arguments.\n";
            return 0;
        }  
        const char *args[2]={current_path_string.c_str(),argv[2]};
        callPython("_commit",2,args);    
    }
    else if (strcmp(argv[1],"log")==0)
    {
        if (argc!=2)
        {
            std::cout<<"Incorrect number of arguments.\n";
            return 0;
        }  
        const char *args[1]={current_path_string.c_str()};
        callPython("_log",1,args);
    }
    else if (strcmp(argv[1],"retrieve")==0)
    {
        if (argc!=4 && argc!=5)
        {
            std::cout<<"Incorrect number of arguments.\n";
            return 0;
        }
        std::filesystem::path file_path = current_path / argv[3];
        std::string file_path_string = file_path.string();
        if (argc==4) 
        {
            std::string empty="";
            const char *args[4]={current_path_string.c_str(),argv[2],file_path_string.c_str(),empty.c_str()};
            callPython("_retrieve",4,args);
        }
        else
        {
            std::filesystem::path loc_path = current_path / argv[4];
            std::string loc_path_string = loc_path.string();
            const char *args[4]={current_path_string.c_str(),argv[2],file_path_string.c_str(),(loc_path_string).c_str()};
            callPython("_retrieve",4,args);
        }
    }
    else if (strcmp(argv[1],"checkout")==0)
    {
        if (argc!=3)
        {
            std::cout<<"Incorrect number of arguments.\n";
            return 0;     
        }
        const char *args[2]={current_path_string.c_str(),argv[2]};
        callPython("_checkout",2,args);
    }
    else if (strcmp(argv[1],"status")==0)
    {
        if (argc!=3)
        {
            std::cout<<"Incorrect number of arguments.\n";
            return 0;
        }
        std::filesystem::path file_path = current_path / argv[2];
        std::string file_string = file_path.string();
        const char *args[2]={current_path_string.c_str(),file_string.c_str()};
        callPython("_status",2,args);
    }
    else if (strcmp(argv[1],"show")==0)
    {
        if (argc!=2)
        {
            std::cout<<"Incorrect number of arguments.\n";
            return 0;       
        }
        const char *args[1]={current_path_string.c_str()};
        callPython("_show",1,args);
    }
    else if (strcmp(argv[1],"restore")==0)
    {
        if (argc!=3)
        {
            std::cout<<"Incorrect number of arguments.\n";
            return 0;
        }
        std::filesystem::path file_path = current_path / argv[2];
        std::string file_path_string = file_path.string();
        std::string last="last";
        const char *args[4]={current_path_string.c_str(),last.c_str(),file_path_string.c_str(),file_path_string.c_str()};
        callPython("_retrieve",4,args);
    }
    else if (strcmp(argv[1],"help")==0)
    {
        if (argc!=3)
        {
            std::cout<<main_info;
            for (std::string command : command_list)
            {
                std::cout<<command<<"\n";
            }      
            return 0;         
        }
        int i=0;
        for (std::string command : command_list)
        {
            if (strcmp(command.c_str(),argv[2])==0)
            {
                std::cout<<help_info[i]<<"\n";
                return 0;
            }
            i++;
        }
        std::cout<<"No command called "<<argv[2]<<"\nTry one of:\n";
        for (std::string command : command_list)
        {
            std::cout<<command<<"\n";
        }       
    }
    else
    {
        std::cout<<"Invalid command name.\nEnter one of:\n";
        for (std::string command : command_list)
        {
            std::cout<<command<<"\n";
        }
    }
    return 0;
}