CFLAGS = -lcv -lhighgui

all: video

pompom: pompom.cpp
	g++ $(CFLAGS) -o $@ $<
