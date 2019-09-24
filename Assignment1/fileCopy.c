#include <stdio.h>

#define BUFF_SIZE 1024

int main(int argc, char **argv){
	FILE *f1, *f2, *flog;
	char buffer[BUFF_SIZE];
	int size;

	if ((f1 = fopen(argv[1],"r")) == NULL){
		printf("fopen error\n");
		return -1;
	}

	f2 = fopen(argv[2], "w");
	while((size = fread(buffer,sizeof(char),sizeof(buffer),f1)) >0 ){
		fwrite(buffer, sizeof(char), size, f2);
	}

	//char log_buffer[] = "file copy is done";
	flog = fopen("log.txt", "w");
	//fwrite(log_buffer, sizeof(char), sizeof(log_buffer)-1, flog);
	fprintf(flog, "file copy is done");

	fclose(f1);
	fclose(f2);
	fclose(flog);
	
	return 0;	
}
