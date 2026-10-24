# The installer's Qt style "veltos-installer" (installerstyle.cpp).
# SPDX-License-Identifier: GPL-3.0-or-later
cmake_minimum_required(VERSION 3.16)
project(veltos-installer-style LANGUAGES CXX)

find_package(Qt6 6.4 REQUIRED COMPONENTS Widgets)
set(CMAKE_AUTOMOC ON)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(veltos-installer-style MODULE installerstyle.cpp)
target_compile_options(veltos-installer-style PRIVATE -Wall -Wextra)
target_link_libraries(veltos-installer-style PRIVATE Qt6::Widgets)
install(TARGETS veltos-installer-style LIBRARY DESTINATION ${QT6_INSTALL_PLUGINS}/styles)
