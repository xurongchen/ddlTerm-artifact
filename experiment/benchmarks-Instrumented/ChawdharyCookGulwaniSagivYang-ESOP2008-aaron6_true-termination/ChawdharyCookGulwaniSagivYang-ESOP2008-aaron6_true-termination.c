#include <stdio.h>
#include <stdlib.h>

int _nondet_int() {
    return rand();
}
int _nondet_2() {
    return rand()%2;
}
int main() {
    int x, tx, y, ty, n;
    scanf("%d%d%d%d%d", &x, &tx, &y, &ty, &n);
    printf("[Testing] <Interface V4.0> (Log all variables for reuse)\n");
    if (x + y >= 0) {
  while (x <= n && x >= 2 * tx + y && y >= ty + 1 && x >= tx + 1) {
      printf("x:%d,tx:%d,y:%d,ty:%d,n:%d\n", x, tx, y, ty, n);
    if (_nondet_2() != 0) {
      tx = x;
      ty = y;
      x = _nondet_int();
      y = _nondet_int();
    } else {
      tx = x;
      x = _nondet_int();
    }
  }
  }
  return 0;
}
