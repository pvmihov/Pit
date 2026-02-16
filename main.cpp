#include<iostream>
#include<cstring>
#include<filesystem>
#include<Python.h>
std::string command_list[8]={
    "help", "init", "add", "commit", "log", "retrieve", "checkout", "status"
};
std::string install_folder="INSERT_folder";
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
        PyObject* pFunc = PyObject_GetAttrString(pModule, "_init");
        if (pFunc==nullptr || !PyCallable_Check(pFunc))
        {
            if (PyErr_Occurred()) PyErr_Print();
            std::cerr<<"Couldn't find _init function in communicator.py";
            Py_DECREF(pModule);
            return 1;
        }
        PyObject* pArgs = PyTuple_New(1);
        PyObject* pathValue = PyUnicode_FromString(current_path_string.c_str());
        PyTuple_SetItem(pArgs, 0, pathValue); ///this steal the refrence, so when we decref pArgs, it will decref pathValue
        PyObject* pResult = PyObject_CallObject(pFunc, pArgs);
        if (pResult == nullptr)
        {
            PyErr_Print();
            Py_DECREF(pModule);
            Py_DECREF(pArgs);
            Py_DECREF(pFunc);
        }
        Py_DECREF(pModule);
        Py_DECREF(pArgs);
        Py_DECREF(pFunc);  
        Py_DECREF(pResult);
        std::string cppResult = PyUnicode_AsUTF8(pResult);
        std::cout<<cppResult<<"\n";
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
        PyObject* pFunc = PyObject_GetAttrString(pModule, "_log");
        if (pFunc==nullptr || !PyCallable_Check(pFunc))
        {
            if (PyErr_Occurred()) PyErr_Print();
            std::cerr<<"Couldn't find _init function in communicator.py";
            Py_DECREF(pModule);
            return 1;
        }
        PyObject* pArgs = PyTuple_New(1);
        PyObject* pathValue = PyUnicode_FromString(current_path_string.c_str());
        PyTuple_SetItem(pArgs, 0, pathValue); ///this steal the refrence, so when we decref pArgs, it will decref pathValue
        PyObject* pResult = PyObject_CallObject(pFunc, pArgs);
        if (pResult == nullptr)
        {
            PyErr_Print();
            Py_DECREF(pModule);
            Py_DECREF(pArgs);
            Py_DECREF(pFunc);
        }
        Py_DECREF(pModule);
        Py_DECREF(pArgs);
        Py_DECREF(pFunc);  
        Py_DECREF(pResult);
        std::string cppResult = PyUnicode_AsUTF8(pResult);
        std::cout<<cppResult<<"\n";
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
        std::cout<<"I am about to do a checkout to branch "<<argv[2]<<"\n";
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
    return 0;
}