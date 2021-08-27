CMAKE_MINIMUM_REQUIRED(VERSION 2.8.11)

SET(PROJECTNAME RBOT)
PROJECT(${PROJECTNAME})

SET(CMAKE_VERBOSE_MAKEFILE ON)

SET(OpenCV_STATIC OFF)


SET(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH}
	"${CMAKE_CURRENT_SOURCE_DIR}/cmake_modules/")

SET(CMAKE_INCLUDE_CURRENT_DIR ON)
SET(CMAKE_AUTOMOC ON)

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

# Below, I tell CMake where to find the libraries.
# The "debug" and "optimized" keywords tell CMake which version to use for
# debug and release builds, respectively.
# Obviously, you'll have to edit this part to point to the libraries' locations
# on your computer.
# I _think_ some of these can also be added to the System path instead, but I
# am not entirely sure how you would handle the debug/release switching then.
Set(OpenCV_DIR debug "D:/Libraries/opencv/out/build/x64-Debug" optimized "D:/Libraries/opencv/out/build/x64-Release")
Set(Qt5_DIR "D:/Programs/Qt/5.15.1/msvc2019_64/lib/cmake/Qt5")
Set(ASSIMP_LIBRARIES debug "D:/Libraries/assimp/out/build/x64-Debug/code/assimp-vc142-mtd.lib" optimized "D:/Libraries/assimp/out/build/x64-Release/code/assimp-vc142-mt.lib")
Set(ASSIMP_INCLUDE_DIR debug "D:/Libraries/assimp/out/build/x64-Debug/include" optimized "D:/Libraries/assimp/out/build/x64-Release/include")
Set(ASSIMP_INCLUDE_DIR_CONFIG "D:/Libraries/assimp/include")


FIND_PACKAGE(OpenGL REQUIRED)
FIND_PACKAGE(OpenCV REQUIRED)
# This change in syntax was required to get the Qt stuff working for me,
# but I don't remember exactly why at the time of this writing.
FIND_PACKAGE(Qt5 COMPONENTS Widgets REQUIRED)
FIND_PACKAGE(Qt5 COMPONENTS OpenGL REQUIRED)
# FIND_PACKAGE(ASSIMP REQUIRED)

SET(LIBRARIES 
	Qt5::Widgets 
	Qt5::OpenGL
	${OpenCV_LIBS}
	${OPENGL_LIBRARIES}
	${ASSIMP_LIBRARIES}
)

# The below, when uncommented, prints out the libs included and the includes.
# If you need to debug this CMAKE file, you can uncomment them.

# message("OpenCV Dir:")
# message(${OpenCV_DIR})
# message("Assimp Libs:")
# message(${ASSIMP_LIBRARIES})
# message("Assimp Include:")
# message(${ASSIMP_INCLUDE_DIR})
# message("OpenCV Libs:")
# message(${OpenCV_LIBS})
# message("OpenCV Include:")
# message(${OpenCV_INCLUDE_DIRS})

INCLUDE_DIRECTORIES(
	${OpenCV_INCLUDE_DIRS} 
	${OPENGL_INCLUDE_DIR}
	${ASSIMP_INCLUDE_DIR}
	${ASSIMP_INCLUDE_DIR_CONFIG}
)


ADD_EXECUTABLE(${PROJECTNAME} ${SOURCES})

TARGET_LINK_LIBRARIES(${PROJECTNAME} ${LIBRARIES})

