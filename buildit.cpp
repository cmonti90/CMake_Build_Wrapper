#include "buildit.h"

#include <cstdlib>
#include <stdexcept>
#include <cstring>
#include <iostream>

int main(int argc, char *argv[])
{
    (void)argc;
    (void)argv;

    std::vector<std::string> parsedArgs;

    parseArgs(argc, argv, parsedArgs); 

    const char *buildDir = std::getenv("SIM_DIR");

    if (buildDir == nullptr)
    {
        const char *err_msg = "SIM_DIR environment variable not set";
        throw std::runtime_error(err_msg);
    }

    std::cout << "buildDir = " << buildDir << std::endl;

    std::string cmd;

    cmd = "cmake -S " + std::string(buildDir) + " -B " + std::string(buildDir) + "/build/release -DCMAKE_BUILD_TYPE=Release";
    system(cmd.c_str());

    cmd = "cmake --build " + std::string(buildDir) + "/build/release";
    system(cmd.c_str());

    return 0;
}

void parseArgs(const int argc, const char* argv, std::vector<std::string> &parsedArgs)
{
    std::string arg;
    bool argPopulated{false};
    bool isStr{false};
    bool isChar{false};

    for (int i = 0; i < argc; ++i)
    {
        while (argv[i] != ' ' || isStr || isChar)
        {
            arg.push_back(argv[i]);
            ++i;
        }

        parsedArgs.push_back(arg);
    }
}