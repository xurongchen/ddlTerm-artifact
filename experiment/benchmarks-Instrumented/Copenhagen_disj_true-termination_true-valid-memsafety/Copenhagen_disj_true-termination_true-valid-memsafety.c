#include<stdio.h>

int main()
{
    int x, y, oldx;
    scanf("%d%d", &x, &y);
    printf("[Testing] <Interface V4.0> (Log all variables for reuse)\n");

    if(!(-1073741823<=x && x<=1073741823)) return 0;
    if(!(-1073741823<=y && y<=1073741823)) return 0;

    while (x >= 0 || y >= 0)
    {
        printf("x:%d,y:%d,oldx:%d\n", x, y, oldx);

		oldx = x;
		x = y - 1;
		y = oldx - 1;
    }
    return 0;
}
