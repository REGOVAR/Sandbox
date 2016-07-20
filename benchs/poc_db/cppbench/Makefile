CXX = g++ 

LDFLAGS = -Lvcflib/lib \
	  -Lvcflib/tabixpp/htslib \
	  -lvcflib -lhts -lz -lpthread -lm

INCLUDE = -I vcflib/include -I vcflib/tabixpp/htslib

CCFLAGS = -Wall -Wextra -pedantic -std=c++11

all: import_regovar

vcflib/lib/libvcflib.a : 
	make -C vcflib openmp

import_regovar: main.cpp vcflib/lib/libvcflib.a 
	$(CXX) -Wall -o $@ $<  $(LDFLAGS) $(INCLUDE)

clean:
	rm -f import_regovar
	make -C vcflib clean
