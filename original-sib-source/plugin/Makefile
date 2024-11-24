CC ?= clang
CXX ?= clang++
CXXFLAGS = -fPIC -Wall -Wextra -Wno-unused-parameter -O3 -flto=full -I/usr/lib/llvm-15/include

LDFLAGS = -flto=full

.PHONY: all
all: plugin.so tool

plugin.so: PPCallbacks.o plugin.o
	$(CXX) $(LDFLAGS) -shared -o $@ $^

tool: plugin.o tool.o PPCallbacks.o
	$(CXX) $(LDFLAGS) -lclang-cpp -lLLVM -o $@ $^

.PHONY: format
format:
	clang-format -style=file -i *.cpp *.hpp

.PHONY: clean
clean:
	@rm -f plugin.so tool *.o
