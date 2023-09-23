#ifndef F8C90C92_A92D_425F_ADB3_0DCCDEA8A3CD
#define F8C90C92_A92D_425F_ADB3_0DCCDEA8A3CD

#include <vector>
#include <string>

enum class BuildMode : unsigned int
{
    Unset,
    Configure,
    Build,
    Clean,
    Help
};

BuildMode buildMode;
std::string buildType;
std::string sourceDir;
std::string buildDir;
std::string buildXtraArgs;

void parseArgs(int argc, char *argv[]);
bool buildFileExists(const std::string &dir);
void createBuildFile(const std::string &dir);
void readBuildFile(const std::string &dir);
std::string trim(const std::string& line);

#endif /* F8C90C92_A92D_425F_ADB3_0DCCDEA8A3CD */
