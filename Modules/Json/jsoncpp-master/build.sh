mkdir -p build/release
cd build/release
cmake -DCMAKE_BUILD_TYPE=release -DBUILD_STATIC_LIBS=OFF -DBUILD_SHARED_LIBS=ON -DARCHIVE_INSTALL_DIR=. -G "Unix Makefiles" ../..
make
cp ./src/lib_json/libjsoncpp* ../../../lib/Linux/
cp ./src/lib_json/libjsoncpp* ../../../../../src/ImgProc/GameRecognize/Lib/
cp ./src/lib_json/libjsoncpp* ../../../../../bin/
