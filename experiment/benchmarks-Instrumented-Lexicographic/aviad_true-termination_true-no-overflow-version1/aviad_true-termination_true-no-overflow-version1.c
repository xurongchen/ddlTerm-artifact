#include <stdio.h>

int main()
{
  int a;
  scanf("%d", &a);
  printf("[Testing] <Interface V3.0TR> (Basic lexical method)\n");

  while (a > 1)
  {
    printf("%d\n", a);

    if (a % 2 == 0)
      {
printf("L1\n");a = a / 2;}
    else if (a % 3 == 0)
      {
printf("L2\n");a = a / 3;}
    else
      {
printf("L3\n");a = a + 1;}
  }
  return 0;
}
