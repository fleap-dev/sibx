CC = clang-15
CXX = clang++-15
CXXFLAGS = -fPIC -Wall -Wextra -Wno-unused-parameter $(shell llvm-config-15 --cxxflags) -std=gnu++17 -O3 -flto=full
LDFLAGS = $(shell llvm-config-15 --ldflags) -flto=full
LIBS = $(shell llvm-config-15 --libs all) -lclang

.PHONY: all
all: plugin.so 

plugin.o: plugin.hpp MyRecursiveASTVisitor.hpp

plugin.so: plugin.o
	$(CXX) $(LDFLAGS) -shared -o $@ $^ ${LIBS}

tool: tool.o plugin.o
	$(CXX) $(LDFLAGS) -lLLVM -o $@ $^ ${LIBS}

.PHONY: format
format:
	clang-format -style=file -i *.cpp *.hpp

.PHONY: clean
clean:
	@rm -f plugin.so tool *.o
