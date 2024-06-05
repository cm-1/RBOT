cmake_minimum_required(VERSION 3.14)

project(RBOT VERSION 0.1 LANGUAGES CXX)

SET(CMAKE_VERBOSE_MAKEFILE ON)

SET(OpenCV_STATIC OFF)



#set(CMAKE_INCLUDE_CURRENT_DIR ON)

# This is the same as before, except I've moved shaders to their own directory
# for the sake of convenience.
FILE(GLOB SOURCES src/*.cpp src/*.h src/*.hpp shaders/*.glsl)

# The executable will need access to the shaders, frame, and .obj at a
# local path. So, we'll need to copy these files to the executable's location.

# This first command gets a list of all of the files that we need to copy.
FILE(GLOB RESOURCE_FILES RELATIVE ${CMAKE_SOURCE_DIR}
    shaders/*.glsl
	data/frame.png
	data/squirrel_demo_low.obj
)

# This command gets the location of the executable.
# It comes from the original CMakeLists.txt, but I moved it up to use it
# before the next command.
SET(EXECUTABLE_OUTPUT_PATH ${PROJECT_BINARY_DIR}/bin)

# Finally, this command copies each file in the list to the right location.
foreach(RESOURCE_FILE ${RESOURCE_FILES})
	configure_file(${RESOURCE_FILE} ${EXECUTABLE_OUTPUT_PATH}/${RESOURCE_FILE} COPYONLY)
endforeach()

FIND_PACKAGE(OpenGL REQUIRED)

message("Searching for OpenCV and ASSIMP installs.")
message("If not found, make sure they are installed (not just built) and consider setting CMAKE_PREFIX_PATH to point to them.")
message("E.G., could look like C:\\Libraries\\opencv-480;C:\\Libraries\\assimp-524;")
# If CMake cannot find these libraries, set a CMAKE_PREFIX_PATH to point to them.
# E.g., on my computer, it is: "C:\Libraries\opencv-480;C:\Libraries\assimp-524;"
FIND_PACKAGE(OpenCV REQUIRED)
FIND_PACKAGE(ASSIMP REQUIRED)
SET(CMAKE_AUTOMOC ON)

add_compile_definitions(QT_DEPRECATED_WARNINGS)

# Not entirely sure both OpenGL and Widgets are required; there may be a more
# minimal version of the below, but I don't have time right now to learn/test.
FIND_PACKAGE(QT NAMES Qt6 Qt5 COMPONENTS OpenGL Widgets REQUIRED)
FIND_PACKAGE(Qt${QT_VERSION_MAJOR} COMPONENTS OpenGL Widgets REQUIRED)

SET(RBOT_DEPENDENCY_LIBRARIES 
        Qt${QT_VERSION_MAJOR}::Widgets
        Qt${QT_VERSION_MAJOR}::OpenGL
        ${OpenCV_LIBS}
        ${OPENGL_LIBRARIES}
        ${ASSIMP_LIBRARIES}
    )
ADD_EXECUTABLE(RBOT ${SOURCES})


target_compile_options(RBOT PUBLIC -fsanitize=undefined)
target_link_options(RBOT PUBLIC -fsanitize=undefined)


target_link_libraries(RBOT
  PRIVATE
    ${RBOT_DEPENDENCY_LIBRARIES}
)

set_target_properties(RBOT PROPERTIES
    MACOSX_BUNDLE_GUI_IDENTIFIER my.example.com
    MACOSX_BUNDLE_BUNDLE_VERSION ${PROJECT_VERSION}
    MACOSX_BUNDLE_SHORT_VERSION_STRING ${PROJECT_VERSION_MAJOR}.${PROJECT_VERSION_MINOR}
)

