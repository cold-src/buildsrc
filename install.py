#!/usr/bin/python3

#
# buildsrc Install Script
#

import os

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
    append_end += "/// buildsrc end ///"

    return append_start + content + append_end, True

# entry point #
def main():
    # find project dir
    root_project_dir = os.path.abspath(find_root_project_dir())
    print("found root project dir (w/ settings.gradle): " + root_project_dir)

    # open settings.gradle
    settingsFile = os.path.join(root_project_dir, "settings.gradle")
    print("opened settings.gradle")
    with open(settingsFile, 'r+') as f:
        content = f.read()
        f.seek(0, 0)
        content, modified = install_settings_gradle_content(content)
        if modified:
            f.write(content)
            print("gradle.settings: new content installed and written")
        else:
            print("gradle.settings: no install necessary")

    # print success
    print("successfully installed buildsrc into proj(" + root_project_dir + ")")

if __name__ == "__main__":
    main()