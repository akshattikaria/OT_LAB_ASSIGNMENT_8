#include <stddef.h>
double row_sum(const double *a, size_t n) {
    double total = 0.0;
    for (size_t i=0; i<n; ++i)
        for (size_t j=0; j<n; ++j) total += a[i*n+j];
    return total;
}
double column_sum(const double *a, size_t n) {
    double total = 0.0;
    for (size_t j=0; j<n; ++j)
        for (size_t i=0; i<n; ++i) total += a[i*n+j];
    return total;
}
double blocked_sum(const double *a, size_t n) {
    double total = 0.0;
    const size_t tile=32;
    for (size_t ii=0; ii<n; ii+=tile)
        for (size_t jj=0; jj<n; jj+=tile)
            for (size_t i=ii; i<n && i<ii+tile; ++i)
                for (size_t j=jj; j<n && j<jj+tile; ++j) total += a[i*n+j];
    return total;
}
