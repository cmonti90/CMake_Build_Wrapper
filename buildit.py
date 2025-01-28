
import argparse as ap
import os
import sys
from enum import Enum


class BuildOpts(Enum):
    CONFIG = ("Config", 0b0001)
    BUILD = ("Build", 0b0010)
    DEBUG = ("Debug", 0b0100)
    RELEASE = ("Release", 0b1000)
    CLEAN = ("Clean", 0b10000)


    @staticmethod
    def print_enum():
        for opt in BuildOpts:
            print(f'{opt.name}: {opt.value[0]}, {opt.value[1]}')


    def __init__(self, build_mode = None, build_config = None, build_clean = False):
        self.opts = 0

        if build_clean:
            self.opts += BuildOpts.CLEAN.value[1]

        if build_mode is not None:
            if BuildOpts.has_opt_static(build_mode, BuildOpts.CONFIG):
                self.opts += build_mode.value[1]

            elif BuildOpts.has_opt_static(build_mode, BuildOpts.BUILD):
                self.opts += build_mode.value[1]

            else:
                raise ValueError(f'Invalid build mode: {build_mode}\n\nValid options:\n{BuildOpts.print_enum()}')
        
        if build_config is not None:
            if BuildOpts.has_opt_static(build_config, BuildOpts.DEBUG):
                self.opts += build_config.value[1]

            elif BuildOpts.has_opt_static(build_config, BuildOpts.RELEASE):
                self.opts += build_config.value[1]

            else:
                raise ValueError(f'Invalid build configuration: {build_config}\n\nValid options:\n{BuildOpts.print_enum()}')
    

    def has_opt(self, opt):
        return self.opts & opt.value[1] == opt.value[1]


    @staticmethod
    def has_opt_static(opts, opt):
        return opts & opt.value[1] == opt.value[1]
    

    def __str__(self):
        result = []

        for opt in BuildOpts:
                    if self.opts & opt.value[1]:
                        result.append(opt.value[0])

        return ', '.join(result)
    
    def string(self):
        return self.__str__()

    def numeric(self):
        return self.value[1]


def main():
    parser = ap.ArgumentParser(description='Builds a project')
    parser.add_argument('project', help='The project to build')
    parser.add_argument('config', help='The configuration to build')
    args = parser.parse_args()

    project = args.project
    config = args.config

    print(f'Building {project} with configuration {config}...')

    if not os.path.exists(project):
        print(f'Error: Project {project} does not exist')
        sys.exit(1)

    if not os.path.exists(f'{project}/{config}.json'):
        print(f'Error: Configuration {config} does not exist for project {project}')
        sys.exit(1)

    print(f'Build complete for {project} with configuration {config}')

    return 0


if __name__ == '__main__':
    sys.exit(main())