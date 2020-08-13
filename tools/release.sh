#!/bin/sh


if [ $# -lt 1 ]; then
	echo "Please set release dir!"
fi

RELEASE_DIR=$1

mkdir -p $RELEASE_DIR

cp -rf ../bin $RELEASE_DIR
cp -rf ../cfg $RELEASE_DIR
cp -rf ../data $RELEASE_DIR
cp -rf ../log $RELEASE_DIR
mkdir -p $RELEASE_DIR/tools
cp -rf ../tools/SDKTool $RELEASE_DIR/tools
cp -f ../*.txt $RELEASE_DIR

chmod +x $RELEASE_DIR/bin/*.sh
chmod +x $RELEASE_DIR/bin/UIRecognize  
chmod +x $RELEASE_DIR/bin/GameReg