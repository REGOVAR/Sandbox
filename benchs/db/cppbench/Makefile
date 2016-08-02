.PHONY: all clean

CXX = g++

LDFLAGS = \
	-Lvcflib/lib \
	-Lvcflib/tabixpp/htslib \
	-lvcflib -lhts -lz -lpthread -lm \
	-lpqxx -lpq

INCLUDE = \
	-I vcflib/include \
	-I vcflib/tabixpp/htslib \

CCFLAGS = -Wall -Wextra -pedantic -std=c++11

VCFLIB = vcflib/lib/libvcflib.a

BIN=import_regovar

SRC = \
	main.cpp

OBJ = $(SRC:.cpp=.o)

all: $(BIN)

$(VCFLIB):
	make -C vcflib openmp

%.o: %.cpp $(VCFLIB)
	$(CXX) $(CCFLAGS) -c -o $@ $<  $(INCLUDE)

$(BIN): $(OBJ)
	$(CXX) -o $@ $^ $(LDFLAGS)

clean:
	rm -f $(BIN) *.o
	make -C vcflib clean
