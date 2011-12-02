CFLAGS = -g -Wall -lcv -lhighgui

all: pompom

pompom: pompom.cpp
	g++ $(CFLAGS) -o $@ $<

.PHONY: clean
clean:
	rm -f pompom
