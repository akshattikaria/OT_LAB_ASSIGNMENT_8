#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
#include <omp.h>

static int row_at(const int64_t *row, int n, int64_t index) {
    int lo=0,hi=n;
    while(lo+1<hi){int middle=(lo+hi)/2;if(row[middle]<=index)lo=middle;else hi=middle;}
    return lo;
}

int main(int argc,char **argv){
    if(argc!=2)return 2;
    FILE *file=fopen(argv[1],"rb");if(!file)return 3;
    int64_t header[3];if(fread(header,sizeof(int64_t),3,file)!=3)return 4;
    int n=(int)header[0],columns=(int)header[1];int64_t nnz=header[2];
    int64_t *row=malloc((n+1)*sizeof(int64_t));int32_t *col=malloc(nnz*sizeof(int32_t));
    double *val=malloc(nnz*sizeof(double)),*x=malloc(columns*sizeof(double)),*y=calloc(n,sizeof(double)),*reference=calloc(n,sizeof(double));
    if(!row||!col||!val||!x||!y||!reference)return 5;
    if(fread(row,sizeof(int64_t),n+1,file)!=(size_t)n+1||fread(col,sizeof(int32_t),nnz,file)!=(size_t)nnz||fread(val,sizeof(double),nnz,file)!=(size_t)nnz||fread(x,sizeof(double),columns,file)!=(size_t)columns)return 6;
    fclose(file);omp_set_num_threads(2);
    for(int i=0;i<n;i++)for(int64_t j=row[i];j<row[i+1];j++)reference[i]+=val[j]*x[col[j]];
    int tile=256;
    for(int method=0;method<2;method++){
        for(int repeat=-1;repeat<7;repeat++){
            double begin=omp_get_wtime();
            for(int i=0;i<n;i++)y[i]=0;
            if(method==0){
                #pragma omp parallel for schedule(static)
                for(int i=0;i<n;i++){double sum=0;for(int64_t j=row[i];j<row[i+1];j++)sum+=val[j]*x[col[j]];y[i]=sum;}
            }else{
                int64_t tiles=(nnz+tile-1)/tile;
                #pragma omp parallel for schedule(dynamic,1)
                for(int64_t t=0;t<tiles;t++){
                    int64_t first=t*tile,last=first+tile;if(last>nnz)last=nnz;int i=row_at(row,n,first);
                    for(int64_t j=first;j<last;){
                        int64_t end=row[i+1]<last?row[i+1]:last;double sum=0;
                        while(j<end){sum+=val[j]*x[col[j]];j++;}
                        #pragma omp atomic update
                        y[i]+=sum;
                        i++;
                    }
                }
            }
            double elapsed=omp_get_wtime()-begin,error=0;
            for(int i=0;i<n;i++){double e=fabs(y[i]-reference[i]);if(e>error)error=e;}
            if(error>1e-8)return 7;
            if(repeat>=0)printf("{\"method\":%d,\"repeat\":%d,\"seconds\":%.12g,\"tile\":%d,\"max_error\":%.12g}\n",method,repeat,elapsed,tile,error);
            if(method==1){int proposed=(int)(nnz*0.000005/(elapsed*2));if(proposed<32)proposed=32;if(proposed>4096)proposed=4096;tile=(proposed/32)*32;}
        }
    }
    free(row);free(col);free(val);free(x);free(y);free(reference);return 0;
}
