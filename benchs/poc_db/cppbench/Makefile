CXX = g++ 

LDFLAGS = -Lvcflib/lib \
	      -Ltabixpp/htslib\
	      -lvcflib -lhts -lz -lpthread -lm

INCLUDE = -I vcflib/include 

CCFLAGS = -Wall -Wextra -pedantic -std=c++11

all: import_regovar

vcflib/lib/libvcflib.a : 
	make -C vcflib 

import_regovar: main.cpp vcflib/lib/libvcflib.a 
	$(CXX) -Wall -o $@ $<  $(LDFLAGS) $(INCLUDE)

clean:
	rm -f import_regovar