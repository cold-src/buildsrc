#!/usr/bin/python3

#
# buildsrc Tool Script
#

import os
import sys

## Find the root project directory
## which is the directory which contains settings.gradle
def find_root_project_dir():
    curr_dir = "./"
    while not os.path.exists(curr_dir + "/settings.gradle") and curr_dir:
        curr_dir = curr_dir + "../"
    if not curr_dir:
        print("failed to find root project path (dir with settings.gradle)")
        os._exit(-1)
    return curr_dir

### Fix the content of settings.gradle
def install_settings_gradle_content(content: str):
    # check if fixing is necessary
    if "/// buildsrc" in content:
        return content, False

    # build content to append
    append_start = ""

    append_start += "/// buildsrc start ///"
    append_start += """
pluginManagement {
    repositories {
        gradlePluginPortal()
        maven { url 'https://papermc.io/repo/repository/maven-public/'}
    }
}
""" # add paperweight repository
    append_start += "/// buildsrc end ///\n\n"

    append_end = "\n"
    append_end += "/// buildsrc start ///\n"
    append_end += "include 'buildsrc'\n" # include buildsrc module
    append_end += "/// buildsrc end ///\n"

    return append_start + content + append_end, True

## Execute the installation process
def install(root_project_dir):
    print("installing buildsrc into proj(" + root_project_dir + ")")

    # open settings.gradle
    settingsFile = os.path.join(root_project_dir, "settings.gradle")
    print("opened settings.gradle")
    with open(settingsFile, 'a+') as f:
        content = f.read()
        f.seek(0, 0)
        print(content)
        content, modified = install_settings_gradle_content(content)
        if modified:
            f.write(content)
            print("gradle.settings: new content installed and written")
        else:
            print("gradle.settings: no install necessary")

    # print success
    print("successfully installed buildsrc into proj(" + root_project_dir + ")")

## Wizard Object: for storing the current property state
class ModuleProperties:
    def __init__(self) -> None:
        self.has_paper = False
        self.version = '1.0.0'

## Start the new module wizard
## for creating a new module
def new_module_wiz(root_project_dir, name):
    print("wizard: create module " + name + " in project")
    props = ModuleProperties()
    cmd = "____"
    while not cmd.isspace() and not cmd in [ 'exit', 'done', 'end', 'e', 'confirm' ]:
        # input command
        cmd = input("wizard new-module $ ")

        # cancel
        if cmd == 'cancel' or cmd == 'c':
            print("new module create cancelled")
            return

        # split
        splitCmd = cmd.split(" ")
        match splitCmd[0]:
            case 'hasPaper', 'p':
                print("new-module: hasPaper set")
                props.has_paper = True
            case 'version', 'v':
                print("new-module: version = " + splitCmd[1])
                props.version = splitCmd[1]

    # create subdirectory
    module_dir = os.path.join(root_project_dir, name)
    print("creating module dir at: " + module_dir)
    os.makedirs(module_dir, exist_ok=True)
    
    # create build.gradle
    buildFile = os.path.join(module_dir, "build.gradle")
    with open(buildFile, 'a+') as f:
        print("creating build.gradle in module dir")

        # generate content #
        content = ""
        content += """
/* Init by new-module, buildsrc/tool.py */

plugins {
    // java
    id 'java'
    id 'java-library'

    // package publishing
    id 'maven-publish'
    id 'signing'

    // for shading in dependencies
    id "com.github.johnrengelman.shadow" version "7.1.2"
""" # general plugins
        
        if props.has_paper:
            content += "\n\n\tid ('io.papermc.paperweight.userdev') version '1.3.5'"

        content += "\n}\n" # close plugins

        content += "version '" + props.version + "'\n"

        content += "\next {\n"
        if props.has_paper:
            content += "\thasPaper = true\n"
        content += "}\n"

        content += "\napply from: '" + os.path.relpath(root_project_dir + "/buildsrc", module_dir) + "/module.gradle" + "', to: project\n"

        # write content to file
        f.write(content)

        print("created build.gradle in module dir")

    # include in settings.gradle
    settingsFile = os.path.join(root_project_dir, "settings.gradle")
    with open(settingsFile, 'a+') as f:
        content = f.read()
        
        content += "\ninclude '" + name + "'\n"

        f.write(content)
        print("modified settings.gradle to include module")
    

# entry point #
def main(argv):
    # find project dir
    root_project_dir = os.path.abspath(find_root_project_dir())
    print("found root project dir (w/ settings.gradle): " + root_project_dir)
    
    # check subcommand
    if len(argv) <= 1:
        print("please specify a subcommand")
        sys.exit(-1)
    if argv[1] == 'install':
        install(root_project_dir)
    elif argv[1] == 'new-module' or argv[1] == 'nm':
        new_module_wiz(root_project_dir, argv[2])
    else:
        print("unknown subcommand: " + argv[1])
        sys.exit(-1)
    print("done.")

if __name__ == "__main__":
    main(sys.argv)