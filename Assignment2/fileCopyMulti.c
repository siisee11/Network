#include <stdio.h>
#include <pthread.h>
#include <unistd.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>

#define BUFF_SIZE 1024
#define STRING_SIZE 100

typedef struct fName{
	char input[100];
	char output[100];
}FNAME;

void *work(void *);

pthread_mutex_t mutex;
pthread_mutex_t mutex_sync;
pthread_cond_t cond_sync;
time_t t;

int main(){
	FNAME fname; 
	int id = 0;
	char input_file_name[STRING_SIZE];
	char output_file_name[STRING_SIZE];
	pthread_t pid;

	pthread_mutex_init(&mutex, NULL);
	pthread_mutex_init(&mutex_sync, NULL);
	pthread_cond_init(&cond_sync, NULL);

	t = time(NULL);

	while(1){
		printf("Input the file name:"); 
		scanf("%s", input_file_name);
		printf("Input the new name:"); 
		scanf("%s", output_file_name);

		strcpy(fname.input,input_file_name);
		strcpy(fname.output,output_file_name);

		// pthread_create
		pthread_mutex_lock(&mutex_sync);
		pthread_create(&pid,NULL,work,(void *)&fname);
		pthread_cond_wait(&cond_sync,&mutex_sync);
		pthread_detach(pid);
		pthread_mutex_unlock(&mutex_sync);
	}
	pthread_mutex_destroy(&mutex);

	return 0;	
}

void *work(void *fname){
	FNAME* filename = (FNAME*)malloc(sizeof(FNAME));
	FILE *f1, *f2, *flog;
	char buffer[BUFF_SIZE];
	int size;

	pthread_mutex_lock(&mutex_sync);
	strcpy(filename->input,((FNAME *)fname)->input); 
	strcpy(filename->output,((FNAME *)fname)->output); 
	pthread_cond_signal(&cond_sync);
	pthread_mutex_unlock(&mutex_sync);

	pthread_mutex_lock(&mutex);
	flog = fopen("log.txt", "a");
	fprintf(flog, "%ld", time(NULL)-t);
	fprintf(flog, " Start copying %s to %s\n", filename->input, filename->output);
	fclose(flog);
	pthread_mutex_unlock(&mutex);

	if ((f1 = fopen(filename->input,"r")) == NULL){
		printf("fopen error\n");
		return NULL;
	}

	f2 = fopen(filename->output, "w");
	while((size = fread(buffer,sizeof(char),sizeof(buffer),f1)) >0 ){
		fwrite(buffer, sizeof(char), size, f2);
	}

	pthread_mutex_lock(&mutex);
	flog = fopen("log.txt", "a");
	fprintf(flog, "%ld", time(NULL)-t);
	fprintf(flog, " %s is copied completely\n", filename->output);
	fclose(flog);
	pthread_mutex_unlock(&mutex);

	fclose(f1);
	fclose(f2);
	
	return NULL;
}

