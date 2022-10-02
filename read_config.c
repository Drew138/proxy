// C program to implement
// the above approach
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Driver code
Config *get_config()
{
	FILE* file;
	char ch;

	// Opening file in reading mode
	file = fopen("config.proxy", "r");

	if (file == NULL) {
		printf("file can't be opened \n");
        return NULL;
	}

	printf("content of this file are \n");

	// Printing what is written in file
	// character by character using loop.
	do {
		ch = fgetc(ptr);
		printf("%c", ch);

		// Checking if character is not EOF.
		// If it is EOF stop eading.
	} while (ch != EOF);

	fclose(ptr);
    struct Config conf;
	// Closing the file
	return conf;
}

