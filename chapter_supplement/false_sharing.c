#include <omp.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
int main(int argc,char **argv) {
    int stride=argc>1?atoi(argv[1]):1;
    if(stride!=1 && stride!=8)return 2;
    _Alignas(64) _Atomic uint64_t counters[16];
    for(int i=0;i<16;i++)atomic_store(&counters[i],0);
    double start=0,finish=0;omp_set_dynamic(0);
    #pragma omp parallel num_threads(2) shared(start,finish,counters)
    {
        int tid=omp_get_thread_num();
        #pragma omp barrier
        #pragma omp master
        start=omp_get_wtime();
        #pragma omp barrier
        for(int i=0;i<1000000;i++)atomic_fetch_add_explicit(&counters[tid*stride],1,memory_order_relaxed);
        #pragma omp barrier
        #pragma omp master
        finish=omp_get_wtime();
    }
    uint64_t sum=atomic_load(&counters[0])+atomic_load(&counters[stride]);
    if(sum!=2000000)return 3;
    printf("%llu %.9f\n",(unsigned long long)sum,finish-start);return 0;
}
