#include "buildit.h"

#include <cstdlib>
#include <cstdint>
#include <stdexcept>
#include <cstring>
#include <iostream>
#include <cctype>
#include <filesystem>
#include <fstream>

void parseArgs( const int argc, const char* argv[] )
{
    std::string arg;
    bool argPopulated{false};
    bool isStr{false};
    bool isChar{false};

    int j{0};

    for ( int i = 1; i < argc; ++i )
    {
        if ( std::string( argv[i] ) == "-c" )
        {
            buildMode = BuildMode::Configure;
            continue;
        }
        else if ( std::string( argv[i] ) == "-cr" )
        {
            buildMode = BuildMode::Configure;
            buildType = "Release";
            continue;
        }
        else if ( std::string( argv[i] ) == "-cd" )
        {
            buildMode = BuildMode::Configure;
            buildType = "Debug";
            continue;
        }
        else if ( std::string( argv[i] ) == "-j" )
        {
            buildMode = BuildMode::Build;
            continue;
        }
        else if ( std::string( argv[i] ) == "-m" )
        {
            buildMode = BuildMode::Clean;
            continue;
        }
        else if ( std::string( argv[i] ) == "-h" )
        {
            printHelp();
            continue;
        }
        else if ( std::string( argv[i] ) == "-s" )
        {
            sourceDir = std::string( argv[++i] );
            continue;
        }
        else if ( std::string( argv[i] ) == "-b" )
        {
            buildDir = std::string( argv[++i] );
            continue;
        }
        else if ( std::string( argv[i] ) == "-v" )
        {
            std::cout << "buildit version 0.1" << std::endl;
            exit( 0 );
        }
        else
        {
            buildXtraArgs += std::string( argv[i] ) + " ";
        }
    }
}

int main( const int argc, const char* argv[] )
{
    try
    {
        sourceDir = trim( std::string( std::getenv( "SIM_DIR" ) ) );
    }
    catch ( ... )
    {
        sourceDir = "";
    }

    buildMode = BuildMode::Unset;
    buildType = "Release";
    buildDir = sourceDir + "/build/";

    parseArgs( argc, argv );

    if ( sourceDir.empty() )
    {
        const char* err_msg = "SIM_DIR environment variable not set";
        throw std::runtime_error( err_msg );
    }
    else if ( sourceDir.back() != '/' )
    {
        sourceDir.append( "/" );
    }

    if ( buildDir.back() != '/' )
    {
        buildDir.push_back( '/' );
    }

    buildDir += buildType + "/";

    std::string cmd;

    switch ( buildMode )
    {
        case BuildMode::Configure:
            {
                createBuildFile( sourceDir );

                cmd = "cmake -S " + sourceDir + " -B " + buildDir + " -DCMAKE_BUILD_TYPE=" + buildType + " -DCMAKE_EXPORT_COMPILE_COMMANDS=ON " + buildXtraArgs;

                std::cout << "Command: " << cmd << std::endl;

                system( cmd.c_str() );

                break;
            }
        case BuildMode::Build:
            {
                if ( buildFileExists( sourceDir ) )
                {
                    readBuildFile( sourceDir );
                }
                else
                {
                    createBuildFile( sourceDir );
                }

                cmd = "cmake --build " + buildDir + buildXtraArgs;

                std::cout << "Command: " << cmd << std::endl;

                system( cmd.c_str() );

                createRunitExec();
                createSimLinksToRunitExec();
                createConfigFile();

                break;
            }
        case BuildMode::Clean:
            {
                    std::cout << "Clearing build directory: " << sourceDir << "build/" << std::endl;

                    cmd = "rm -rf " + sourceDir + "build/";
                    system( cmd.c_str() );

                break;
            }
        case BuildMode::Unset:
        default:
            {
                const char* err_msg = "-c or -m or -j needs to be provided";
                throw std::runtime_error( err_msg );
                break;
            }
    }

    return 0;
}

bool buildFileExists( const std::string& dir )
{
    std::string buildFile = dir + ".buildit.build";

    return std::filesystem::exists( std::filesystem::path( buildFile ) );
}

void createBuildFile( const std::string& dir )
{
    std::string buildFile = dir + ".buildit.build";

    std::ofstream ofs( buildFile, std::ofstream::out );

    ofs << "buildMode = " << static_cast<unsigned int>( buildMode ) << std::endl;
    ofs << "buildType = " << buildType << std::endl;
    ofs << "sourceDir = " << sourceDir << std::endl;
    ofs << "buildDir = " << buildDir << std::endl;

    std::cout << "buildMode = " << static_cast<unsigned int>( buildMode ) << std::endl;
    std::cout << "buildType = " << buildType << std::endl;
    std::cout << "sourceDir = " << sourceDir << std::endl;
    std::cout << "buildDir = " << buildDir << std::endl;

    ofs.close();
}

void readBuildFile( const std::string& dir )
{
    std::string buildFile = dir + ".buildit.build";

    std::ifstream ifs( buildFile, std::ifstream::in );

    std::string line;

    std::getline( ifs, line );
    buildMode = static_cast<BuildMode>( std::stoi( line.substr( line.find( "=" ) + 1 ) ) );

    std::getline( ifs, line );
    buildType = trim( line.substr( line.find( "=" ) + 1 ) );

    std::getline( ifs, line );
    // sourceDir = trim(line.substr(line.find("=") + 1));

    std::getline( ifs, line );
    buildDir = trim( line.substr( line.find( "=" ) + 1 ) );

    if ( buildDir.back() != '/' )
    {
        buildDir.push_back( '/' );
    }

    ifs.close();
}

std::string trim( const std::string& line )
{
    const char* WhiteSpace = " \t\v\r\n";
    std::size_t start = line.find_first_not_of( WhiteSpace );
    std::size_t end = line.find_last_not_of( WhiteSpace );
    return start == end ? std::string() : line.substr( start, end - start + 1 );
}

void printHelp()
{
    std::cout << "buildit -c -cr -cd -j -m -h -s -b -v" << std::endl;
    std::cout << "  -c: configure (release is default)" << std::endl;
    std::cout << "  -cr: configure release" << std::endl;
    std::cout << "  -cd: configure debug" << std::endl;
    std::cout << "  -j: build" << std::endl;
    std::cout << "  -m: clean" << std::endl;
    std::cout << "  -h: help" << std::endl;
    std::cout << "  -s: source directory" << std::endl;
    std::cout << "  -b: build directory" << std::endl;
    std::cout << "  -v: version" << std::endl;
}

void createRunitExec()
{
    execDir = buildDir + "config/";
    std::string runitExec = execDir + "runit.cpp";
    std::string cmd;

    if ( !std::filesystem::exists( std::filesystem::path( execDir ) ) )
    {
        cmd = "mkdir " + execDir;
        system( cmd.c_str() );
    }

    std::ofstream ofs( runitExec, std::ofstream::out );

    ofs << "#include <string>" << std::endl << std::endl;
    ofs << "int main(const int argc, const char* argv[])" << std::endl << std::endl;
    ofs << "{" << std::endl;
    ofs << "std::string cmd;" << std::endl;
    ofs << "cmd = \"python3 " << sourceDir << "Sim/Runner/runit.py \";" << std::endl;
    ofs << "for ( unsigned int i{1u}; i < argc; ++i )" << std::endl;
    ofs << "{" << std::endl;
    ofs << "\tcmd += std::string(argv[i]) + \" \";" << std::endl;
    ofs << "}" << std::endl;
    ofs << std::endl;
    ofs << "system(cmd.c_str());" << std::endl;
    ofs << "return 0;" << std::endl;
    ofs << "}" << std::endl;

    ofs.close();

    cmd = "g++ -std=c++17 -o " + execDir + "runit " + runitExec;
    system( cmd.c_str() );

    cmd = "rm -f " + runitExec;
    system( cmd.c_str() );

}

void createSimLinksToRunitExec()
{
    std::string cmd;

    std::string configDir = sourceDir + "Sim/config/";

    if ( !std::filesystem::exists( std::filesystem::path( configDir ) ) )
    {
        cmd = "mkdir " + sourceDir + "Sim/config";

        system( cmd.c_str() );
    }

    if ( std::filesystem::is_symlink( ( configDir + "exec" ).c_str()))
    {
        cmd = "rm -f " + configDir + "exec";
        system( cmd.c_str() );
    }

    cmd = "ln -s " + execDir + " " + configDir + "exec";
    system( cmd.c_str() );

    if ( std::filesystem::is_symlink( ( buildDir + "config/runnerLink" ).c_str()))
    {
        cmd = "rm -f " + buildDir + "config/runnerLink";
        system( cmd.c_str() );
    }

    cmd = "ln -s " + buildDir + "/Sim/Runner/runner " + buildDir + "config/runnerLink";
    system( cmd.c_str() );
}

void createConfigFile()
{
    std::string configFile = buildDir + "config/config.sh";
    std::string cmd;

    std::ofstream ofs( configFile, std::ofstream::out );

    ofs << "#!/bin/bash" << std::endl;
    ofs << "PATH=${PATH/\"" << sourceDir << "Sim/config/exec:\"/}" << std::endl;

    ofs << "echo \"Prending to PATH: " << sourceDir << "Sim/config/exec\"" << std::endl;
    ofs << "export PATH=\"" << sourceDir << "Sim/config/exec:${PATH}\"" << std::endl;

    ofs.close();
}