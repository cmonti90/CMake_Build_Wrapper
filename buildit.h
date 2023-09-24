#ifndef F8C90C92_A92D_425F_ADB3_0DCCDEA8A3CD
#define F8C90C92_A92D_425F_ADB3_0DCCDEA8A3CD

#include <vector>
#include <string>

enum class BuildMode : unsigned int
{
    Unset,
    Configure,
    Build,
    Clean
};

BuildMode buildMode;
std::string buildType;
std::string sourceDir;
std::string buildDir;
std::string buildXtraArgs;
std::string execDir;

void parseArgs( int argc, char* argv[] );
bool buildFileExists( const std::string& dir );
void createBuildFile( const std::string& dir );
void readBuildFile( const std::string& dir );
std::string trim( const std::string& line );
void createRunitExec();
void createSimLinksToRunitExec();
void createConfigFile();
void printHelp();

#endif /* F8C90C92_A92D_425F_ADB3_0DCCDEA8A3CD */
