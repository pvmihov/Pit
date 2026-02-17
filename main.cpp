#include<iostream>
#include<cstring>
#include<filesystem>
#include<Python.h>
std::string command_list[9]={
    "help", "init", "add", "commit", "log", "retrieve", "checkout", "status", "show"
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
        if (argc==4) std::cout<<"I am about to do a retrieve on "<<argv[2]<<" for "<<file_path.string()<<"\n";
        else
        {
            std::filesystem::path loc_path = current_path / argv[4];
            std::cout<<"I am about to do a retrieve on "<<argv[2]<<" for "<<file_path.string()<<" and store in "<<loc_path.string()<<"\n";
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
        std::cout<<"I am about to try status with "<<file_path.string()<<"\n";
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
    return 0;
}