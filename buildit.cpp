#include <cstdlib>
#include <stdexcept>
#include <cstring>
#include <iostream>
#include <vector>

int main(int agrc, char *argv[])
{
    (void)agrc;
    (void)argv;

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