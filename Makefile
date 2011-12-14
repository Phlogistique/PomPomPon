CFLAGS = -g -Wall -lopencv_core -lopencv_highgui -lopencv_imgproc

all: pompom

pompom: pompom.cpp
	g++ $(CFLAGS) -o $@ $<

.PHONY: clean
clean:
	rm -f pompom
