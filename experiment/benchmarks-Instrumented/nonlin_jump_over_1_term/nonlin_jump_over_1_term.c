#include <stdio.h>

int main() {
  int x, y;
  scanf("%d%d", &x, &y);
  printf("[Testing] <Interface V4.0> (Log all variables for reuse)\n");

  if (y <= 1) return 0;

  while (x >= y) {
    printf("x:%d,y:%d\n", x, y);
    if (x % y == 1) x++;
      else x = x - 2;
  }
  return 0;
}
