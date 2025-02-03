import argparse as ap
import json
import os
import subprocess as sp
import sys

class CMakeCommand:
    """Helper class to run a command (in our case, CMake) via subprocess."""
    def __init__(self, cmd):
        self.cmd = cmd

    def run(self, cwd=None):
        print("Running:", " ".join(self.cmd))

        try:
            sp.check_call(self.cmd, cwd=cwd)
        except sp.CalledProcessError as e:
            print(f"Error: Command failed with return code {e.returncode}")
            sys.exit(1)


def find_project_root(start_dir):
    """
    Walk up the directory tree starting from start_dir until a directory
    without a CMakeLists.txt is encountered. The last directory that contained
    a CMakeLists.txt is assumed to be the project root.
    """

    current = os.path.abspath(start_dir)
    last_with_cmake = None

    while True:
        if os.path.exists(os.path.join(current, "CMakeLists.txt")):
            last_with_cmake = current
        else:
            break
        parent = os.path.dirname(current)

        if parent == current:
            break  # reached the filesystem root

        current = parent

    if last_with_cmake is None:
        # If no CMakeLists.txt was found at all, assume start_dir is the project root.
        return os.path.abspath(start_dir)
    
    return last_with_cmake


def load_buildrc(project_root):
    """Load the JSON configuration from .buildrc in the project root, if it exists."""

    buildrc_path = os.path.join(project_root, ".buildrc")

    if os.path.exists(buildrc_path):
        with open(buildrc_path, "r") as f:
            config = json.load(f)

        return config
    
    return None


def write_buildrc(project_root, config):
    """Write a JSON configuration to .buildrc in the project root."""

    buildrc_path = os.path.join(project_root, ".buildrc")

    with open(buildrc_path, "w") as f:
        json.dump(config, f)

    print(f"Wrote build configuration to {buildrc_path}")


class CMakeWrapper:
    """
    A wrapper around CMake that supports both configuration and building.
    
    Attributes:
      project_root (str): Top‑level project directory (containing CMakeLists.txt).
      build_dir (str): Relative path (from project_root) to the build directory.
      build_type (str): Build type (e.g. Release, Debug, MinRelSize).
      extra_args (list): Extra arguments to pass to CMake.
    """
    def __init__(self, project_root, build_dir, build_type, extra_args=None):
        self.project_root = project_root
        self.build_dir = build_dir      # relative to project_root
        self.build_type = build_type
        self.extra_args = extra_args or []


    def configure(self):
        """
        Configure the project by:
          - Creating the build folder (if needed) in {project_root}/{build_dir}/{build_type}
          - Running CMake with the proper configuration options
          - Writing the .buildrc file in the project root
        """

        # The effective build directory is relative to the project root.
        base_build_dir = os.path.join(self.project_root, self.build_dir, self.build_type)

        if not os.path.exists(base_build_dir):
            os.makedirs(base_build_dir)

        # The configuration command uses the project root as the source.
        cmd = [
            "cmake",
            f"-DCMAKE_BUILD_TYPE={self.build_type}",
            self.project_root
        ] + self.extra_args

        command = CMakeCommand(cmd)
        command.run(cwd=base_build_dir)

        # Write out .buildrc for future builds.
        config = {"build_dir": self.build_dir, "build_type": self.build_type}
        write_buildrc(self.project_root, config)


    def build(self, invoking_dir):
        """
        Build the project (or a subset) by determining the "equivalent" binary
        directory for the invoking directory.
          - If invoked from the project root, build in {project_root}/{build_dir}/{build_type}.
          - If invoked from a subdirectory, compute its relative path from
            the project root and run the build command in the corresponding subdirectory
            of the build folder.
        """

        abs_invoking_dir = os.path.abspath(invoking_dir)
        rel_path = os.path.relpath(abs_invoking_dir, self.project_root)

        if rel_path == ".":
            effective_build_dir = os.path.join(self.project_root, self.build_dir, self.build_type)

        else:
            effective_build_dir = os.path.join(self.project_root, self.build_dir, self.build_type, rel_path)

        if not os.path.exists(effective_build_dir):
            print(f"Error: Build directory '{effective_build_dir}' does not exist. Run configure first [-c].")
            sys.exit(1)

        cmd = [
            "cmake",
            "--build", ".",
            "--config", self.build_type
        ] + self.extra_args

        print(f"Running build command in: {effective_build_dir}")

        command = CMakeCommand(cmd)
        command.run(cwd=effective_build_dir)


def preprocess_args(args, allowed):
    """
    Preprocess wrapper arguments so that any short option of the form
      -XYZ
    where every character in XYZ is in the allowed set, is split into separate flags.
    For example, if allowed = {'c','b','r','d','m'}, then:
      -cr   ->   -c  -r
      -cd   ->   -c  -d
    """

    new_args = []

    for arg in args:

        # Only process single-dash options that are longer than two characters.
        if arg.startswith('-') and not arg.startswith('--') and len(arg) > 2:
            flags = arg[1:]

            if all(ch in allowed for ch in flags):
                for ch in flags:
                    new_args.append('-' + ch)

                continue

        new_args.append(arg)

    return new_args


def parse_arguments():
    """
    Parse command-line arguments.

    Any arguments not recognized by our parser will be passed down to CMake.
    Also, if the bare '--' token is present, all arguments after it are collected
    as extra arguments for CMake.
    """

    args = sys.argv[1:]
    extra_cmake_args = []

    if "--" in args:
        # Everything after '--' goes directly to CMake.
        idx = args.index("--")
        wrapper_args = args[:idx]
        extra_cmake_args = args[idx + 1:]

    else:
        wrapper_args = args

    # Allowed short flags for our wrapper: c, b, r, d, m.
    allowed_short_flags = set("cbrdm")
    wrapper_args = preprocess_args(wrapper_args, allowed_short_flags)

    parser = ap.ArgumentParser(description="CMake wrapper")
    
    parser.add_argument("-S",
                        "--source-dir",
                        default=None,
                        help=("Path to the source directory (project root). "
                              "If not provided, the wrapper will search upward for a CMakeLists.txt"))
    
    parser.add_argument("-B",
                        "--build-dir",
                        default="build",
                        help="Relative path (from project root) to the build directory")

    parser.add_argument("-c",
                        "--configure",
                        action="store_true",
                        help="Run CMake configuration")
    
    parser.add_argument("-b",
                        "--build",
                        action="store_true",
                        help="Run CMake build")
    
    parser.add_argument("-j",
                        type=int,
                        nargs="?",
                        const=1,
                        metavar="Number of jobs",
                        dest="jobs",
                        help="Run CMake build (specify number of jobs)")
    
    parser.add_argument("--del",
                        "--delete",
                        dest="delete",
                        action="store_true",
                        help="Delete the build directory (before configuring/building)")
    

    # Mutually exclusive build-type options.
    group = parser.add_mutually_exclusive_group()

    group.add_argument("--build-type",
                        default="Release",
                        choices=["Release", "Debug", "MinSizeRel", "RelWithDebInfo"],
                        help="Specify the build type")
    
    group.add_argument("-r",
                        "--release",
                        action="store_const",
                        const="Release",
                        dest="build_type",
                        help="Shortcut for --build-type Release")

    group.add_argument("-d",
                        "--debug",
                        action="store_const",
                        const="Debug",
                        dest="build_type",
                        help="Shortcut for --build-type Debug")
    
    group.add_argument("-m",
                        "--minsizerel",
                        action="store_const",
                        const="MinSizeRel",
                        dest="build_type",
                        help="Shortcut for --build-type MinSizeRel")
    

    # Default build type if none of -r/-d/-m/--build-type is specified.
    parser.set_defaults(build_type="Release")

    # Parse the known arguments. Any unknown arguments are collected.
    parsed_args, unknown = parser.parse_known_args(wrapper_args)
    extra_cmake_args = unknown + extra_cmake_args


    # Ensure --build is set when -j is used
    if parsed_args.jobs is not None:
        parsed_args.build = True
        if parsed_args.jobs > 0:
            extra_cmake_args.append(f"-j{parsed_args.jobs}")
        else:
            raise ValueError("The value for -j must be a positive integer.")
        

    return parsed_args, extra_cmake_args


def main():
    parsed_args, extra_args = parse_arguments()

    # If no action is specified, configure only.
    if not parsed_args.delete and not parsed_args.configure and not parsed_args.build:
        parsed_args.configure = True

    # Determine the project root.
    if parsed_args.source_dir:
        project_root = os.path.abspath(parsed_args.source_dir)

        if not os.path.exists(os.path.join(project_root, "CMakeLists.txt")):
            print(f"Error: Provided source directory '{project_root}' does not contain a CMakeLists.txt")
            sys.exit(1)
    else:
        project_root = find_project_root(os.getcwd())

        if not os.path.exists(os.path.join(project_root, "CMakeLists.txt")):
            print("Error: Could not locate a project root with a CMakeLists.txt")
            sys.exit(1)


    # --- Merge command-line options with any existing buildrc values ---
    # Load the existing .buildrc (if present)
    existing_config = load_buildrc(project_root)


    # For build_dir: if provided on command line, use that; otherwise, try buildrc, then default to "build"
    if hasattr(parsed_args, "build_dir"):
        chosen_build_dir = parsed_args.build_dir

    else:
        chosen_build_dir = (existing_config.get("build_dir") if existing_config and "build_dir" in existing_config
                            else "build")
        

    # For build_type: if provided on command line, use that; otherwise, try buildrc, then default to "Release"
    if hasattr(parsed_args, "build_type"):
        chosen_build_type = parsed_args.build_type

    else:
        chosen_build_type = (existing_config.get("build_type") if existing_config and "build_type" in existing_config
                             else "Release")


    # If specified, remove the build directory.
    if parsed_args.delete:
        chosen_build_path = os.path.join(project_root, chosen_build_dir, chosen_build_type)

        if os.path.exists(chosen_build_path):
            print(f"Deleting build directory: {chosen_build_path}")
            sp.check_call(["rm", "-rf", chosen_build_path])


        if os.path.exists(os.path.join(project_root, chosen_build_dir)) and \
            not os.listdir(os.path.join(project_root, chosen_build_dir)):
                os.rmdir(os.path.join(project_root, chosen_build_dir))


        # Remove the .buildrc file.
        if os.path.exists(os.path.join(project_root, ".buildrc")):
            os.remove(os.path.join(project_root, ".buildrc"))


    # If a buildrc already exists but its values differ from the merged values, rewrite it.
    if existing_config is not None:
        if (existing_config.get("build_dir") != chosen_build_dir or
            existing_config.get("build_type") != chosen_build_type):
            new_config = {"build_dir": chosen_build_dir, "build_type": chosen_build_type}
            write_buildrc(project_root, new_config)
            

    # If no buildrc exists, we leave it until a configure is done (which will create one).
    build_dir = chosen_build_dir
    build_type = chosen_build_type


    # Create our wrapper instance.
    wrapper = CMakeWrapper(project_root, build_dir, build_type, extra_args)


    if parsed_args.configure:
        print(f"Configuring project at {project_root}\n"
              f"  Base build directory: '{build_dir}'\n"
              f"  Effective build directory: '{os.path.join(build_dir, build_type)}'\n"
              f"  Build type: '{build_type}'")
        
        wrapper.configure()


    if parsed_args.build:
        invoking_dir = os.getcwd()

        print(f"Building project (or sub‑target) from directory: {invoking_dir}")

        wrapper.build(invoking_dir)


    return 0



if __name__ == '__main__':
    sys.exit(main())
