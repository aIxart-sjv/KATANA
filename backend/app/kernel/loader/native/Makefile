CC = gcc

CFLAGS = -O2 -g -Wall -Wextra

INCLUDES = \
	-I../../skeletons \
	-I../../headers

LIBS = \
	-lbpf \
	-lelf \
	-lz

TARGET = loader

SRC = loader.c

all:
	$(CC) $(CFLAGS) $(INCLUDES) $(SRC) -o $(TARGET) $(LIBS)

clean:
	rm -f $(TARGET)